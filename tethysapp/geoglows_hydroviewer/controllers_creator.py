import json
import os
import shutil
import urllib.parse

import geoglows.streamflow as gsf
import geopandas as gpd
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse
from tethys_sdk.gizmos import SelectInput
from tethys_sdk.permissions import login_required
from tethys_sdk.routing import controller

from .app import GeoglowsHydroviewer as App
from .hydroviewer_creator_tools import get_livingatlas_geojson
from .hydroviewer_creator_tools import get_project_directory
from .hydroviewer_creator_tools import shapefiles_downloaded
from .hydroviewer_creator_tools import walk_upstream

SHAPE_DIR = App.get_custom_setting('global_delineation_shapefiles_directory')

EXPORT_CONFIGS_DICT = {
    'url': '',
    'workspace': '',
    'drainage_layer_name': '',
    'catchment_layer_name': '',
    'zoom': '',
    'center': '',
    'resource_id': '',
    'exported_drainage': False,
    'exported_catchment': False,
}

WARN_DOWNLOAD_SHAPEFILES = 'GEOGloWS Shapefile data not found. You can continue to work on projects who have created ' \
                           'shapefiles but will be unable to create shapefiles for new projects. Check the custom ' \
                           'settings and contact the server admin for help downloading this data.'


@controller(name='geoglows_hydroviewer_creator', url='creator', app_workspace=True)
def home(request, app_workspace):
    if not shapefiles_downloaded():
        messages.warning(request, WARN_DOWNLOAD_SHAPEFILES)

    projects_path = os.path.join(app_workspace.path, 'projects')
    if not os.path.exists(projects_path):
        os.mkdir(projects_path)

    projects = os.listdir(projects_path)
    projects = [(prj.replace('_', ' '), prj) for prj in projects if os.path.isdir(os.path.join(projects_path, prj))]

    if len(projects) > 0:
        show_projects = True
    else:
        show_projects = False

    projects = SelectInput(display_text='Existing Hydroviewer Projects',
                           name='project',
                           multiple=False,
                           options=projects)

    context = {
        'projects': projects,
        'show_projects': show_projects,
    }

    return render(request, 'geoglows_hydroviewer/geoglows_hydroviewer_creator.html', context)


@controller(url='/creator/add-new-project', app_workspace=True)
def add_new_project(request, app_workspace):
    project = request.GET.get('new_project_name', False)
    if not project:
        messages.error(request, 'Please provide a name for the new project')
        return redirect(reverse('geoglows_hydroviewer:geoglows_hydroviewer_creator'))
    project = str(project).replace(' ', '_')
    new_proj_dir = get_project_directory(project, app_workspace)
    try:
        # make a new folder
        os.mkdir(new_proj_dir)
        # make the configs json
        with open(os.path.join(new_proj_dir, 'export_configs.json'), 'w') as ec:
            ec.write(json.dumps(EXPORT_CONFIGS_DICT))
        messages.success(request, 'Project Successfully Created')
        return redirect(reverse('geoglows_hydroviewer:project_overview') +
                        f'?{urllib.parse.urlencode(dict(project=project))}')
    except Exception as e:
        messages.error(request, f'Failed to Create Project: {project} ({e})')
        return redirect(reverse('geoglows_hydroviewer:geoglows_hydroviewer_creator'))


@controller(url='creator/delete_existing_project', app_workspace=True)
def delete_existing_project(request, app_workspace):
    project = request.GET.get('project', False)
    if not project:
        messages.error(request, 'Project not found, please pick from list of projects or make a new one')
    else:
        try:
            shutil.rmtree(os.path.join(app_workspace.path, 'projects', project))
            messages.success(request, f'Successfully Deleted Project: {project}')
        except Exception as e:
            messages.error(request, f'Failed to Delete Project: {project} ({e})')
    return redirect(reverse('geoglows_hydroviewer:geoglows_hydroviewer_creator'))


@controller(url='creator/project', app_workspace=True)
def project_overview(request, app_workspace):
    project = request.GET.get('project', False)
    if not project:
        messages.error(request, 'Project not found, please pick from list of projects or make a new one')
        return redirect(reverse('geoglows_hydroviewer:geoglows_hydroviewer_creator'))
    proj_dir = get_project_directory(project, app_workspace)

    with open(os.path.join(proj_dir, 'export_configs.json')) as a:
        configs = json.loads(a.read())

    boundaries_created = os.path.exists(os.path.join(proj_dir, 'boundaries.json'))

    shapefiles_created = bool(os.path.exists(os.path.join(proj_dir, 'catchment_shapefile.zip')) and
                              os.path.exists(os.path.join(proj_dir, 'drainageline_shapefile.zip')))

    exported = any([configs['exported_drainage'], configs['exported_catchment']])

    context = {
        # project naming
        'project': project,
        'project_title': project.replace('_', ' '),

        # creator step 1
        'boundaries': boundaries_created,
        'boundariesJS': json.dumps(boundaries_created),

        # creator step 2
        'shapefiles': shapefiles_created,
        'shapefilesJS': json.dumps(shapefiles_created),

        # creator step 3
        'exported': exported,
        'exportedJS': json.dumps(exported),

        # config values
        'geoserver_url': configs['url'],
        'workspace': configs['workspace'],
        'drainage_layer': configs['drainage_layer_name'],
        'catchment_layer': configs['catchment_layer_name'],
    }

    return render(request, 'geoglows_hydroviewer/creator_project_overview.html', context)


@controller(url='creator/render', app_workspace=True)
def render_hydroviewer(request, app_workspace):
    project = request.POST.get('project', False)
    project_title = False

    # controls to auto fill form values with project values
    projects_path = os.path.join(app_workspace.path, 'projects')
    projects = os.listdir(projects_path)
    projects = [(prj.replace('_', ' '), prj) for prj in projects if os.path.isdir(os.path.join(projects_path, prj))]
    projects = SelectInput(display_text='Get values from a Hydroviewer project',
                           name='project',
                           multiple=False,
                           options=projects)

    if project:
        exports_config_file_path = os.path.join(get_project_directory(project, app_workspace), 'export_configs.json')
        if os.path.exists(exports_config_file_path):
            project_title = project.replace('_', ' ')
            with open(exports_config_file_path, 'r') as ec:
                configs = json.loads(ec.read())
                url = configs.get('url', '')
                workspace = configs.get('workspace', '')
                dl = configs.get('drainage_layer_name', '')
                ctch = configs.get('catchment_layer_name', '')
                center = configs.get('center', '')
                zoom = configs.get('zoom', '')
    else:
        url = ''
        workspace = ''
        dl = ''
        ctch = ''
        center = ''
        zoom = ''

    context = {
        'project': project,
        'projects': projects,
        'project_title': project_title,
        'url': url,
        'workspace': workspace,
        'dl': dl,
        'ctch': ctch,
        'center': center,
        'zoom': zoom,
    }

    return render(request, 'geoglows_hydroviewer/creator_render_hydroviewer.html', context)


@controller(url='/creator/project/edit/draw_boundaries', app_workspace=True)
def draw_boundaries(request, app_workspace):
    project = request.GET.get('project', False)
    if not project:
        messages.error(request, 'Unable to find this project')
        return redirect(reverse('geoglows_hydroviewer:geoglows_hydroviewer_creator'))

    watersheds_select_input = SelectInput(
        display_text='Select A Watershed',
        name='watersheds_select_input',
        multiple=False,
        original=True,
        options=[['View All Watersheds', ''],
                 ["Islands", "islands-geoglows"],
                 ["Australia", "australia-geoglows"],
                 ["Japan", "japan-geoglows"],
                 ["East Asia", "east_asia-geoglows"],
                 ["South Asia", "south_asia-geoglows"],
                 ["Central Asia", "central_asia-geoglows"],
                 ["West Asia", "west_asia-geoglows"],
                 ["Middle East", "middle_east-geoglows"],
                 ["Europe", "europe-geoglows"],
                 ["Africa", "africa-geoglows"],
                 ["South America", "south_america-geoglows"],
                 ["Central America", "central_america-geoglows"],
                 ["North America", "north_america-geoglows"]],
        initial=''
    )

    context = {
        'project': project,
        'project_title': project.replace('_', ' '),
        'watersheds_select_input': watersheds_select_input,
        'geojson': bool(os.path.exists(os.path.join(get_project_directory(project, app_workspace), 'boundaries.json'))),
    }
    return render(request, 'geoglows_hydroviewer/creator_boundaries_draw.html', context)


@controller(url='creator/project/edit/boundary_by_outlet')
def boundary_by_outlet(request):
    project = request.GET.get('project', False)
    if not project:
        messages.error(request, 'Unable to find this project')
        return redirect(reverse('geoglows_hydroviewer:geoglows_hydroviewer_creator'))
    context = {
        'project': project,
        'project_title': project.replace('_', ' '),
    }
    return render(request, 'geoglows_hydroviewer/creator_boundaries_outlet.html', context)


@controller(url='/creator/project/edit/choose_boundary_country', app_workspace=True)
def choose_boundary_country(request, app_workspace):
    project = request.GET.get('project', False)
    if not project:
        messages.error(request, 'Unable to find this project')
        return redirect(reverse('geoglows_hydroviewer:geoglows_hydroviewer_creator'))

    regions = SelectInput(
        display_text='Pick A World Region (ESRI Living Atlas)',
        name='regions',
        multiple=False,
        original=True,
        options=(('None', ''),
                 ('Antarctica', 'Antarctica'),
                 ('Asiatic Russia', 'Asiatic Russia'),
                 ('Australia/New Zealand', 'Australia/New Zealand'),
                 ('Caribbean', 'Caribbean'),
                 ('Central America', 'Central America'),
                 ('Central Asia', 'Central Asia'),
                 ('Eastern Africa', 'Eastern Africa'),
                 ('Eastern Asia', 'Eastern Asia'),
                 ('Eastern Europe', 'Eastern Europe'),
                 ('European Russia', 'European Russia'),
                 ('Melanesia', 'Melanesia'),
                 ('Micronesia', 'Micronesia'),
                 ('Middle Africa', 'Middle Africa'),
                 ('Northern Africa', 'Northern Africa'),
                 ('Northern America', 'Northern America'),
                 ('Northern Europe', 'Northern Europe'),
                 ('Polynesia', 'Polynesia'),
                 ('South America', 'South America'),
                 ('Southeastern Asia', 'Southeastern Asia'),
                 ('Southern Africa', 'Southern Africa'),
                 ('Southern Asia', 'Southern Asia'),
                 ('Southern Europe', 'Southern Europe'),
                 ('Western Africa', 'Western Africa'),
                 ('Western Asia', 'Western Asia'),
                 ('Western Europe', 'Western Europe'),)
    )

    context = {
        'project': project,
        'project_title': project.replace('_', ' '),
        'regions': regions,
        'geojson': bool(os.path.exists(os.path.join(get_project_directory(project, app_workspace), 'boundaries.json'))),
    }
    return render(request, 'geoglows_hydroviewer/creator_boundaries_choose.html', context)


@controller(url='/creator/project/edit/save_boundaries', app_workspace=True)
def save_boundaries(request, app_workspace):
    proj_dir = get_project_directory(request.POST['project'], app_workspace)

    geojson = request.POST.get('geojson', False)
    esri = request.POST.get('esri', False)
    if geojson:
        with open(os.path.join(proj_dir, 'boundaries.json'), 'w') as gj:
            gj.write(geojson)
    elif esri:
        with open(os.path.join(proj_dir, 'boundaries.json'), 'w') as gj:
            gj.write(get_livingatlas_geojson(esri))
    else:
        return JsonResponse({'status': 'fail'})

    lat = round(float(request.POST.get('center_lat')), 4)
    lon = round(float(request.POST.get('center_lng')), 4)
    with open(os.path.join(proj_dir, 'export_configs.json'), 'r') as a:
        ec = json.loads(a.read())
        ec['zoom'] = request.POST.get('zoom', 4)
        ec['center'] = f'{lat},{lon}'
    with open(os.path.join(proj_dir, 'export_configs.json'), 'w') as a:
        a.write(json.dumps(ec))

    return JsonResponse({'status': 'success'})


@controller(url='/creator/project/edit/find_upstream_boundaries', app_workspace=True)
def find_upstream_boundaries(request, app_workspace):
    project = request.GET.get('project', False)
    reachid = int(request.GET.get('reachid'))
    if not project:
        return JsonResponse({'status': 'error', 'error': 'project not found'})
    proj_dir = get_project_directory(project, app_workspace)

    try:
        # remove the boundaries if they exist
        boundary_json = os.path.join(proj_dir, "boundaries.json")
        if os.path.exists(boundary_json):
            os.remove(boundary_json)

        # figure out the region stream network shapefile to read and then open it
        region = gsf.reach_to_region(reachid)
        zipped_shp = os.path.join(SHAPE_DIR, f'{region}-catchment.zip')
        gdf = gpd.read_file("zip:///" + os.path.join(zipped_shp, f'{region}-catchment.shp'))
        gdf = gdf.to_crs(epsg=4326)
        gdf = gdf[['COMID', 'NextDownID', 'geometry']]

        # traverse the network, select, dissolve
        upstream = walk_upstream(gdf, reachid, 'COMID', 'NextDownID')
        gdf = gdf[gdf['COMID'].isin(upstream)]
        gdf['dissolve'] = 'dissolve'
        gdf = gdf.dissolve(by="dissolve")
        gdf = gdf[['geometry']]
        gdf.to_file(boundary_json, driver='GeoJSON')

        # write the zoom/centroid info to the configs json
        with open(os.path.join(proj_dir, 'export_configs.json'), 'r') as a:
            ec = json.loads(a.read())
            ec['zoom'] = 6
            ec['center'] = f'{gdf.centroid.y[0]},{gdf.centroid.x[0]}'
        with open(os.path.join(proj_dir, 'export_configs.json'), 'w') as a:
            a.write(json.dumps(ec))

        return JsonResponse({'status': 'success'})

    except Exception:
        return JsonResponse({'status': 'fail'})


@controller(name='retrieve_boundaries', url='creator/project/edit/retrieve_boundaries', app_workspace=True)
def retrieve_hydroviewer_boundaries(request, app_workspace):
    proj_dir = get_project_directory(request.GET['project'], app_workspace)
    with open(os.path.join(proj_dir, 'boundaries.json'), 'r') as geojson:
        return JsonResponse(json.load(geojson))
