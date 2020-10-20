import json
import os
import shutil
import urllib.parse

import geopandas as gpd
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse
from tethys_sdk.gizmos import SelectInput
from tethys_sdk.permissions import login_required

from .app import GeoglowsHydroviewer as App
from .hydroviewer_creator_tools import get_project_directory
from .hydroviewer_creator_tools import shapefiles_downloaded

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


@login_required()
def home(request):
    if not shapefiles_downloaded():
        messages.warning(request, WARN_DOWNLOAD_SHAPEFILES)

    projects_path = os.path.join(App.get_app_workspace().path, 'projects')
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


@login_required()
def add_new_project(request):
    project = request.GET.get('new_project_name', False)
    if not project:
        messages.error(request, 'Please provide a name for the new project')
        return redirect(reverse('geoglows_hydroviewer:geoglows_hydroviewer_creator'))
    project = str(project).replace(' ', '_')
    new_proj_dir = get_project_directory(project)
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


@login_required()
def delete_existing_project(request):
    project = request.GET.get('project', False)
    if not project:
        messages.error(request, 'Project not found, please pick from list of projects or make a new one')
    else:
        try:
            shutil.rmtree(os.path.join(App.get_app_workspace().path, 'projects', project))
            messages.success(request, f'Successfully Deleted Project: {project}')
        except Exception as e:
            messages.error(request, f'Failed to Delete Project: {project} ({e})')
    return redirect(reverse('geoglows_hydroviewer:geoglows_hydroviewer_creator'))


@login_required()
def project_overview(request):
    project = request.GET.get('project', False)
    if not project:
        messages.error(request, 'Project not found, please pick from list of projects or make a new one')
        return redirect(reverse('geoglows_hydroviewer:geoglows_hydroviewer_creator'))
    proj_dir = get_project_directory(project)

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


@login_required()
def render_hydroviewer(request):
    project = request.POST.get('project', False)
    project_title = False

    # contols to auto fill form values with project values
    projects_path = os.path.join(App.get_app_workspace().path, 'projects')
    projects = os.listdir(projects_path)
    projects = [(prj.replace('_', ' '), prj) for prj in projects if os.path.isdir(os.path.join(projects_path, prj))]
    projects = SelectInput(display_text='Get values from a Hydroviewer project',
                           name='project',
                           multiple=False,
                           options=projects)

    if project:
        exports_config_file_path = os.path.join(get_project_directory(project), 'export_configs.json')
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


@login_required()
def draw_hydroviewer_boundaries(request):
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
        'geojson': bool(os.path.exists(os.path.join(get_project_directory(project), 'boundaries.json'))),
    }
    return render(request, 'geoglows_hydroviewer/creator_boundaries_draw.html', context)


@login_required()
def save_boundaries(request):
    proj_dir = get_project_directory(request.POST['project'])

    with open(os.path.join(proj_dir, 'boundaries.json'), 'w') as gj:
        gj.write(request.POST.get('geojson'))

    lat = round(float(request.POST.get('center_lat')), 4)
    lon = round(float(request.POST.get('center_lng')), 4)
    with open(os.path.join(proj_dir, 'export_configs.json'), 'r') as a:
        ec = json.loads(a.read())
        ec['zoom'] = request.POST.get('zoom', 4)
        ec['center'] = f'{lat},{lon}'
    with open(os.path.join(proj_dir, 'export_configs.json'), 'w') as a:
        a.write(json.dumps(ec))

    gjson_file = gpd.read_file(os.path.join(proj_dir, 'boundaries.json'))
    gjson_file = gjson_file.to_crs("EPSG:3857")
    gjson_file.to_file(os.path.join(proj_dir, 'projected_boundaries'))
    return JsonResponse({'status': 'success'})


@login_required()
def choose_hydroviewer_boundaries(request):
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
        'geojson': bool(os.path.exists(os.path.join(get_project_directory(project), 'boundaries.json'))),
    }
    return render(request, 'geoglows_hydroviewer/creator_boundaries_choose_predefined.html', context)


@login_required()
def retrieve_hydroviewer_boundaries(request):
    proj_dir = get_project_directory(request.GET['project'])
    with open(os.path.join(proj_dir, 'boundaries.json'), 'r') as geojson:
        return JsonResponse(json.load(geojson))


@login_required()
def upload_boundary(request):
    project = request.POST.get('project', False)
    if not project:
        return JsonResponse({'status': 'error', 'error': 'project not found'})
    proj_dir = get_project_directory(project)

    # make the projected selections folder
    tmp_dir = os.path.join(proj_dir, 'projected_boundaries')
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.mkdir(tmp_dir)

    # save the uploaded shapefile to that folder
    files = request.FILES.getlist('files')
    for file in files:
        file_name = 'projected_boundaries' + os.path.splitext(file.name)[-1]
        with open(os.path.join(tmp_dir, file_name), 'wb') as dst:
            for chunk in file.chunks():
                dst.write(chunk)

    # read the uploaded shapefile with geopandas and save it to selections.geojson
    boundaries_gdf = gpd.read_file(os.path.join(tmp_dir, 'projected_boundaries.shp'))
    boundaries_gdf = boundaries_gdf.to_crs("EPSG:3857")
    boundaries_gdf.to_file(os.path.join(tmp_dir, 'projected_boundaries.shp'))
    boundaries_gdf = boundaries_gdf.to_crs("EPSG:4326")
    boundaries_gdf.to_file(os.path.join(proj_dir, "boundaries.json"), driver='GeoJSON')

    return JsonResponse({'status': 'success'})
