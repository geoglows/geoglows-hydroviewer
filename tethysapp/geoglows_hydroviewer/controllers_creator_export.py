import json
import os
import urllib.parse

import geoglows
import geoserver.util
import hs_restclient
import jinja2
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect, reverse
from geoserver.catalog import Catalog
from tethys_sdk.permissions import login_required

from .app import GeoglowsHydroviewer as App
from .hydroviewer_creator_tools import get_project_directory

SHAPE_DIR = App.get_custom_setting('global_delineation_shapefiles_directory')


@login_required()
def export_geoserver(request):
    project = request.GET.get('project', False)
    url = request.GET.get('gs_url')
    username = request.GET.get('gs_username', 'admin')
    password = request.GET.get('gs_password', 'geoserver')
    workspace_name = request.GET.get('workspace', 'geoglows_hydroviewer_creator')
    dl_name = request.GET.get('dl_name', 'drainagelines')
    ct_name = request.GET.get('ct_name', 'catchments')
    if not project:
        return JsonResponse({'error': 'unable to find the project'})
    proj_dir = get_project_directory(project)

    # add keys to the export_configs.json
    with open(os.path.join(proj_dir, 'export_configs.json'), 'r') as configfile:
        geoserver_configs = json.loads(configfile.read())
        geoserver_configs['url'] = url.replace('/rest/', '/wms')
        geoserver_configs['workspace'] = workspace_name
        geoserver_configs['dl'] = dl_name
        geoserver_configs['ctch'] = ct_name
        export_dl_status = geoserver_configs['exported_drainagelines']
        export_ctch_status = geoserver_configs['exported_catchment']
    

    try:
        cat = Catalog(url, username=username, password=password)

        # identify the geoserver stores
        workspace = cat.get_workspace(workspace_name)

        if not export_dl_status:
            try:
                # create geoserver store and upload the drainagelines
                zip_path = os.path.join(proj_dir, 'drainageline_shapefile.zip')
                print('Did you upload this correctly?')
                cat.create_featurestore(dl_name, workspace=workspace, data=zip_path, overwrite=True)
                print('Please work, I want to graduate')
            except Exception as e:
                print('failed to upload drainagelines')
                print(e)
            
            geoserver_configs['exported_drainagelines'] = True
            # Add code to overwrite export_configs.json on successful upload
            
        elif not export_ctch_status:
            try:
                # create geoserver store and upload the catchments
                zip_path = os.path.join(proj_dir, 'catchment_shapefile.zip')
                print('Hey, is this working?')
                cat.create_featurestore(ct_name, workspace=workspace, data=zip_path, overwrite=True)
                print('Just checking stuff')
            except Exception as e:
                print('failed to upload catchments')
                print(e)
            
            geoserver_configs['exported_catchment'] = True

        with open(os.path.join(proj_dir, 'export_configs.json'), 'w') as configfile:
            configfile.write(json.dumps(geoserver_configs))

            # Add code to overwrite export_configs.json on successful upload

    except Exception as e:
        print(e)
        return JsonResponse({'status': 'failed'})

    return JsonResponse({'status': 'success'})

@login_required()
def export_zipfile(request):
    project = request.GET.get('project', False)
    if not project:
        return JsonResponse({'error': 'unable to find the project'})
    proj_dir = get_project_directory(project)

    zip_path = os.path.join(proj_dir, f'{request.GET.get("component")}_shapefile.zip')
    zip_file = open(zip_path, 'rb')
    response = HttpResponse(zip_file, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{request.GET.get("component")}_shapefile.zip"'
    return response


@login_required()
def export_hydroshare(request):
    project = request.POST.get('project', False)
    if project is False:
        messages.error(request, 'Project not found. Please pick a valid project.')
        return redirect(reverse('geoglows_hydroviewer:geoglows_hydroviewer_creator'))
    proj_dir = get_project_directory(project)

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
        geoserver_configs['dl'] = 'drainageline_shapefile drainagelines'
        geoserver_configs['ctch'] = 'catchment_shapefile catchments'
        geoserver_configs['exported'] = True
    with open(os.path.join(proj_dir, 'export_configs.json'), 'w') as configfile:
        configfile.write(json.dumps(geoserver_configs))
        return redirect(reverse('geoglows_hydroviewer:project_overview') +
                        f'?{urllib.parse.urlencode(dict(project=project))}')


@login_required()
def export_html(request):
    template_path = os.path.join(App.get_app_workspace().path, 'hydroviewer_interactive_template.html')

    title = request.POST.get('title')
    html_path = os.path.join(App.get_app_workspace().path, f'{title}.html')

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
