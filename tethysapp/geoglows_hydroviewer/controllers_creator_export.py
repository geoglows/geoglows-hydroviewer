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
from .hydroviewer_creator_tools import zip_project_shapefiles

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

    try:
        cat = Catalog(url, username=username, password=password)

        # identify the geoserver stores
        workspace = cat.get_workspace(workspace_name)

        try:
            # create geoserver store and upload the catchments
            shapefile_plus_sidecars = geoserver.util.shapefile_and_friends(
                os.path.join(proj_dir, 'selected_catchment', 'catchment_select'))
            cat.create_featurestore(ct_name, workspace=workspace, data=shapefile_plus_sidecars, overwrite=True)
        except Exception as e:
            print('failed to upload catchments')
            print(e)

        try:
            # create geoserver store and upload the drainagelines
            shapefile_plus_sidecars = geoserver.util.shapefile_and_friends(
                os.path.join(proj_dir, 'selected_drainageline', 'drainageline_select'))
            cat.create_featurestore(dl_name, workspace=workspace, data=shapefile_plus_sidecars, overwrite=True)
        except Exception as e:
            print('failed to upload drainagelines')
            print(e)

        # add keys to the export_configs.json
        with open(os.path.join(proj_dir, 'export_configs.json'), 'r') as configfile:
            geoserver_configs = json.loads(configfile.read())
            geoserver_configs['url'] = url.replace('/rest/', '/wms')
            geoserver_configs['workspace'] = workspace_name
            geoserver_configs['dl'] = dl_name
            geoserver_configs['ctch'] = ct_name
        with open(os.path.join(proj_dir, 'export_configs.json'), 'w') as configfile:
            configfile.write(json.dumps(geoserver_configs))
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
    zip_path = os.path.join(proj_dir, 'hydroviewer_shapefiles.zip')

    # if there is already a zip file, serve it for download
    if not os.path.exists(zip_path):
        try:
            zip_project_shapefiles(project)
        except Exception as e:
            raise e
    zip_file = open(zip_path, 'rb')
    response = HttpResponse(zip_file, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="hydroviewer_shapefiles.zip"'
    return response


@login_required()
def export_hydroshare(request):
    project = request.POST.get('project', False)
    if project is False:
        messages.error(request, 'Project not found. Please pick a valid project.')
        return redirect(reverse('geoglows_hydroviewer:geoglows_hydroviewer_creator'))
    proj_dir = get_project_directory(project)
    zip_path = os.path.join(proj_dir, 'hydroviewer_shapefiles.zip')

    # make the zip file of shapefiles if it doesn't already exist
    if not os.path.exists(zip_path):
        try:
            zip_project_shapefiles(project)
        except Exception as e:
            raise e

    # hs = hs_restclient.get_oauth_hs(request)
    auth = hs_restclient.HydroShareAuthBasic(username=request.POST.get('username'),
                                             password=request.POST.get('password'))
    hs = hs_restclient.HydroShare(auth=auth)

    try:
        resource_id = hs.createResource('GenericResource',
                                        request.POST.get('title'),
                                        resource_file=zip_path,
                                        keywords=request.POST.get('keywords').split(', '),
                                        abstract=request.POST.get('abstract'), )
        hs.resource(resource_id).functions.unzip(
            payload={'zip_with_rel_path': 'hydroviewer_shapefiles.zip', 'remove_original_zip': True})

        hs.setAccessRules(resource_id, public=True)
        messages.success(request, f'Successfully Exported To New Hydroshare Resource (ID: {resource_id})')

        # add keys to the export_configs.json
        with open(os.path.join(proj_dir, 'export_configs.json'), 'w') as configfile:
            geoserver_configs = json.loads(configfile.read())
            geoserver_configs['url'] = 'https://geoserver.hydroshare.org/geoserver/wms'
            geoserver_configs['workspace'] = f'HS-{resource_id}'
            geoserver_configs['dl'] = 'selected_drainageline drainageline_select'
            geoserver_configs['ctch'] = 'selected_catchment catchment_select'
        with open(os.path.join(proj_dir, 'export_configs.json'), 'w') as configfile:
            configfile.write(json.dumps(geoserver_configs))
            return redirect(reverse('geoglows_hydroviewer:project_overview') +
                            f'?{urllib.parse.urlencode(dict(project=project))}')
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


@login_required()
def export_html(request):
    template_path = os.path.join(App.get_app_workspace().path, 'hydroviewer_interactive_template.html')

    title = request.POST.get('title')
    html_path = os.path.join(App.get_app_workspace().path, f'{title}.html')

    esridependency = any([request.POST.get('esri-imagery', False), request.POST.get('esri-hybrid', False)])

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
                )
            )

    with open(html_path, 'r') as htmlfile:
        response = HttpResponse(htmlfile, content_type='text/html')
        response['Content-Disposition'] = f'attachment; filename="hydroviewer.html"'

    os.remove(html_path)
    return response
