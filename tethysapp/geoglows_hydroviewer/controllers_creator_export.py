import json
import os
import urllib.parse

import geoglows
import hs_restclient
import jinja2
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect, reverse
from geoserver.catalog import Catalog
from tethys_sdk.permissions import login_required
from tethys_sdk.routing import controller

from .app import GeoglowsHydroviewer as App
from .hydroviewer_creator_tools import get_project_directory

SHAPE_DIR = App.get_custom_setting('global_delineation_shapefiles_directory')


@controller(url='/creator/project/export/geoserver', app_workspace=True)
def export_geoserver(request, app_workspace):
    project = request.POST.get('project', False)
    workspace_name = request.POST.get('workspace', 'geoglows_hydroviewer_creator')
    store_name = request.POST.get('store_name', 'shapefilestore')
    store_name = str(store_name).replace(' ', '_')
    store_name = str.lower(store_name)
    if not project:
        return JsonResponse({'error': 'unable to find the project'})
    proj_dir = get_project_directory(project, app_workspace)

    # tailor the geoserver url
    url = request.POST.get('gs_url')
    if not url[-1] == '/':
        url += '/'

    # add keys to the export_configs.json
    with open(os.path.join(proj_dir, 'export_configs.json'), 'r') as configfile:
        geoserver_configs = json.loads(configfile.read())
        geoserver_configs['url'] = url.replace('/rest/', f'/{workspace_name}/wms')
        geoserver_configs['workspace'] = workspace_name
        geoserver_configs['drainage_layer_name'] = str.lower(project) + '_drainagelines'
        geoserver_configs['catchment_layer_name'] = str.lower(project) + '_catchments'

    if geoserver_configs['exported_drainage'] and geoserver_configs['exported_catchment']:
        geoserver_configs['exported_drainage'] = False
        geoserver_configs['exported_catchment'] = False

    try:
        cat = Catalog(url,
                      username=request.POST.get('gs_username', 'admin'),
                      password=request.POST.get('gs_password', 'geoserver'))
        # identify the geoserver stores
        workspace = cat.get_workspace(workspace_name)
    except Exception as e:
        print(e)
        return JsonResponse({'status': 'failed'})

    if not geoserver_configs['exported_drainage']:
        try:
            # create geoserver store and upload the drainagelines
            zip_path = os.path.join(proj_dir, 'drainageline_shapefile.zip')
            cat.create_featurestore(store_name, workspace=workspace, data=zip_path, overwrite=True)
            geoserver_configs['exported_drainage'] = True
            with open(os.path.join(proj_dir, 'export_configs.json'), 'w') as configfile:
                configfile.write(json.dumps(geoserver_configs))
        except Exception as e:
            print('failed to upload drainagelines')
            print(e)

    elif not geoserver_configs['exported_catchment']:
        try:
            # create geoserver store and upload the catchments
            zip_path = os.path.join(proj_dir, 'catchment_shapefile.zip')
            cat.add_data_to_store(store_name, store_name, data=zip_path, workspace=workspace, overwrite=False)
            geoserver_configs['exported_catchment'] = True
            with open(os.path.join(proj_dir, 'export_configs.json'), 'w') as configfile:
                configfile.write(json.dumps(geoserver_configs))
        except Exception as e:
            print('failed to upload catchments')
            print(e)

    return JsonResponse({'status': 'success'})


@controller(url='/creator/project/export/zipfile', app_workspace=True)
def export_zipfile(request, app_workspace):
    project = request.GET.get('project', False)
    if not project:
        return JsonResponse({'error': 'unable to find the project'})
    proj_dir = get_project_directory(project, app_workspace)

    zip_path = os.path.join(proj_dir, f'{request.GET.get("component")}_shapefile.zip')
    with open(zip_path, 'rb') as zip_file:
        response = HttpResponse(zip_file, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{request.GET.get("component")}_shapefile.zip"'
        return response


@controller(url='/creator/project/export/hydroshare', app_workspace=True)
def export_hydroshare(request, app_workspace):
    project = request.POST.get('project', False)
    if project is False:
        messages.error(request, 'Project not found. Please pick a valid project.')
        return redirect(reverse('geoglows_hydroviewer:geoglows_hydroviewer_creator'))
    proj_dir = get_project_directory(project, app_workspace)

    # verify the shapefile zips exist
    catchment_zip = os.path.join(proj_dir, 'catchment_shapefile.zip')
    drainageline_zip = os.path.join(proj_dir, 'drainageline_shapefile.zip')
    if not all([os.path.exists(catchment_zip), os.path.exists(drainageline_zip)]):
        if os.path.exists(catchment_zip):
            os.remove(catchment_zip)
        if os.path.exists(drainageline_zip):
            os.remove(drainageline_zip)
        raise FileNotFoundError('Zipped shapefiles not found')

    try:
        # hs = hs_restclient.get_oauth_hs(request)
        auth = hs_restclient.HydroShareAuthBasic(username=request.POST.get('username'),
                                                 password=request.POST.get('password'))
        hs = hs_restclient.HydroShare(auth=auth)

        resource_id = hs.createResource('GenericResource',
                                        request.POST.get('title'),
                                        resource_file=drainageline_zip,
                                        keywords=request.POST.get('keywords').split(', '),
                                        abstract=request.POST.get('abstract'), )
        hs.addResourceFile(resource_id, catchment_zip)
        hs.resource(resource_id).functions.unzip(
            payload={'zip_with_rel_path': 'catchment_shapefile.zip', 'remove_original_zip': True})
        hs.resource(resource_id).functions.unzip(
            payload={'zip_with_rel_path': 'drainageline_shapefile.zip', 'remove_original_zip': True})

        hs.setAccessRules(resource_id, public=True)
        messages.success(request, f'Successfully Exported To New Hydroshare Resource (ID: {resource_id})')

    except hs_restclient.HydroShareArgumentException as e:
        print('invalid parameter')
        print(e)
        raise e
    except hs_restclient.HydroShareNotAuthorized as e:
        print('hydroshare not authorized')
        print(e)
        raise e
    except hs_restclient.HydroShareHTTPException as e:
        print('unanticipated HTTP error')
        print(e)
        raise e

    # add keys to the export_configs.json
    with open(os.path.join(proj_dir, 'export_configs.json'), 'r') as configfile:
        geoserver_configs = json.loads(configfile.read())
        geoserver_configs['url'] = 'https://geoserver.hydroshare.org/geoserver/wms'
        geoserver_configs['workspace'] = f'HS-{resource_id}'
        geoserver_configs['drainage_layer_name'] = 'drainageline_shapefile ' + str.lower(project) + '_drainagelines'
        geoserver_configs['catchment_layer_name'] = 'catchment_shapefile ' + str.lower(project) + '_catchments'
        geoserver_configs['exported_drainage'] = True
        geoserver_configs['exported_catchment'] = True
    with open(os.path.join(proj_dir, 'export_configs.json'), 'w') as configfile:
        configfile.write(json.dumps(geoserver_configs))
        return redirect(reverse('geoglows_hydroviewer:project_overview') +
                        f'?{urllib.parse.urlencode(dict(project=project))}')


@controller(url='/creator/project/export/html', app_workspace=True)
def export_html(request, app_workspace):
    template_path = os.path.join(app_workspace.path, 'hydroviewer_interactive_template.html')

    title = request.POST.get('title')
    html_path = os.path.join(app_workspace.path, f'{title}.html')

    esridependency = any([request.POST.get('esri-imagery', False),
                          request.POST.get('esri-hybrid', False),
                          request.POST.get('esri-terrain', False),
                          request.POST.get('esri-terrain-labeled', False), ])

    with open(template_path) as template:
        with open(html_path, 'w') as hydrohtml:
            hydrohtml.write(
                jinja2.Template(template.read()).render(
                    title=title,
                    # geoglows data endpoint
                    api_endpoint=geoglows.streamflow.ENDPOINT,
                    # data services and map configs
                    geoserver_wms_url=request.POST.get('url'),
                    workspace=request.POST.get('workspace'),
                    catchment_layer=request.POST.get('ctch'),
                    drainage_layer=request.POST.get('dl'),
                    center=request.POST.get('center', '0, 0'),
                    zoom=request.POST.get('zoom', 5),
                    # basemaps
                    openstreetmap=bool(request.POST.get('openstreetmap', False)),
                    stamenterrain=bool(request.POST.get('stamen-terrain', False)),
                    stamenwatercolor=bool(request.POST.get('stamen-watercolor', False)),
                    esridependency=esridependency,
                    esriimagery=bool(request.POST.get('esri-imagery', False)),
                    esrihybrid=bool(request.POST.get('esri-hybrid', False)),
                    esriterrain=bool(request.POST.get('esri-terrain', False)),
                    esriterrainlabeled=bool(request.POST.get('esri-terrain-labeled', False)),
                )
            )

    with open(html_path, 'r') as htmlfile:
        response = HttpResponse(htmlfile, content_type='text/html')
        response['Content-Disposition'] = f'attachment; filename="hydroviewer.html"'

    os.remove(html_path)
    return response
