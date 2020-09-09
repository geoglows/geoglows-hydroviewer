import glob
import json
import os
import shutil
import urllib.parse

import geomatics
import geopandas as gpd
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse
from tethys_sdk.gizmos import SelectInput
from tethys_sdk.permissions import login_required

from .app import GeoglowsHydroviewer as App
from .hydroviewer_creator_tools import get_project_directory, shapefiles_downloaded

SHAPE_DIR = App.get_custom_setting('global_delineation_shapefiles_directory')

WARN_DOWNLOAD_SHAPEFILES = 'GEOGloWS Shapefile data not found. You can continue to work on projects who have created ' \
                           'shapefiles but will be unable to create shapefiles for new projects. Check the custom ' \
                           'settings and contact the server admin for help downloading this data.'


@login_required()
def home(request):
    if not shapefiles_downloaded():
        messages.warning(request, WARN_DOWNLOAD_SHAPEFILES)

    projects_path = os.path.join(App.get_app_workspace().path, 'projects')
    projects = os.listdir(projects_path)

    projects = [prj for prj in projects if os.path.isdir(os.path.join(projects_path, prj))]
    finished_prjs = [prj for prj in projects if os.path.exists(os.path.join(projects_path, prj, 'hydroviewer.html'))]

    projects = [(prj.replace('_', ' '), prj) for prj in projects]
    finished_prjs = [(prj.replace('_', ' '), prj) for prj in finished_prjs]

    if len(projects) > 0:
        show_projects = True
    else:
        show_projects = False
    if len(finished_prjs) > 0:
        show_finished_projects = True
    else:
        show_finished_projects = False

    projects = SelectInput(display_text='Existing Hydroviewer Projects',
                           name='project',
                           multiple=False,
                           options=projects)
    downloadable_projects = SelectInput(display_text='Download Finished Hydroviewer',
                                        name='downloadable_projects',
                                        multiple=False,
                                        options=finished_prjs)

    context = {
        'projects': projects,
        'downloadable_projects': downloadable_projects,
        'show_projects': show_projects,
        'show_finished_projects': show_finished_projects,
    }

    return render(request, 'geoglows_hydroviewer/geoglows_hydroviewer_creator.html', context)


@login_required()
def add_new_project(request):
    project = request.GET.get('new_project_name', False)
    if not project:
        messages.error(request, 'Please provide a name for the new project')
        return redirect(reverse('geoglows_hydroviewer:geoglows_hydroviewer_creator'))
    project = str(project).replace(' ', '_')
    new_proj_dir = os.path.join(App.get_app_workspace().path, 'projects', project)
    try:
        os.mkdir(new_proj_dir)
        messages.success(request, 'Project Successfully Created')
        return redirect(
            reverse('geoglows_hydroviewer:project_overview') + f'?{urllib.parse.urlencode(dict(project=project))}')
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

    # check to see what data has been created (i.e. which of the steps have been completed)
    boundaries_created = os.path.exists(os.path.join(proj_dir, 'boundaries.json'))

    shapefiles_created = bool(
        os.path.exists(os.path.join(proj_dir, 'selected_catchment')) and
        os.path.exists(os.path.join(proj_dir, 'selected_drainageline'))
    )

    geoserver_configs = os.path.exists(os.path.join(proj_dir, 'geoserver_config.json'))
    if geoserver_configs:
        with open(os.path.join(proj_dir, 'geoserver_config.json')) as a:
            configs = json.loads(a.read())
        geoserver_url = configs['url']
        workspace = configs['workspace']
        drainagelines_layer = configs['dl_layer']
        catchment_layer = configs['ctch_layer']
    else:
        geoserver_url = ''
        workspace = ''
        drainagelines_layer = ''
        catchment_layer = ''

    context = {
        'project': project,
        'project_title': project.replace('_', ' '),

        'boundaries': boundaries_created,
        'boundariesJS': json.dumps(boundaries_created),

        'shapefiles': shapefiles_created,
        'shapefilesJS': json.dumps(shapefiles_created),

        'geoserver': geoserver_configs,
        'geoserverJS': json.dumps(geoserver_configs),
        'geoserver_url': geoserver_url,
        'workspace': workspace,
        'drainagelines_layer': drainagelines_layer,
        'catchment_layer': catchment_layer,
    }

    return render(request, 'geoglows_hydroviewer/creator_project_overview.html', context)


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
def save_drawn_boundaries(request):
    proj_dir = get_project_directory(request.POST['project'])

    geojson = request.POST.get('geojson', False)
    if geojson is not False:
        with open(os.path.join(proj_dir, 'boundaries.json'), 'w') as gj:
            gj.write(geojson)

    esri = request.POST.get('esri', False)
    if esri is not False:
        with open(os.path.join(proj_dir, 'boundaries.json'), 'w') as gj:
            gj.write(json.dumps(geomatics.data.get_livingatlas_geojson(esri)))

    gjson_file = gpd.read_file(os.path.join(proj_dir, 'boundaries.json'))
    gjson_file = gjson_file.to_crs("EPSG:3857")
    gjson_file.to_file(os.path.join(proj_dir, 'projected_selections'))
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
def upload_boundary_shapefile(request):
    project = request.POST.get('project', False)
    if not project:
        return JsonResponse({'status': 'error', 'error': 'project not found'})
    proj_dir = get_project_directory(project)

    # make the projected selections folder
    tmp_dir = os.path.join(proj_dir, 'projected_selections')
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.mkdir(tmp_dir)

    # save the uploaded shapefile to that folder
    files = request.FILES.getlist('files')
    for file in files:
        file_name = 'projected_selections' + os.path.splitext(file.name)[-1]
        with open(os.path.join(tmp_dir, file_name), 'wb') as dst:
            for chunk in file.chunks():
                dst.write(chunk)

    # read the uploaded shapefile with geopandas and save it to selections.geojson
    boundaries_gdf = gpd.read_file(os.path.join(tmp_dir, 'projected_selections.shp'))
    boundaries_gdf = boundaries_gdf.to_crs("EPSG:3857")
    boundaries_gdf.to_file(os.path.join(tmp_dir, 'projected_selections.shp'))
    boundaries_gdf = boundaries_gdf.to_crs("EPSG:4326")
    boundaries_gdf.to_file(os.path.join(proj_dir, "boundaries.json"), driver='GeoJSON')

    return JsonResponse({'status': 'success'})


@login_required()
def geoprocess_hydroviewer_idregion(request):
    project = request.GET.get('project', False)
    if not project:
        raise FileNotFoundError('project directory not found')
    proj_dir = get_project_directory(project)
    gjson_gdf = gpd.read_file(os.path.join(proj_dir, 'projected_selections', 'projected_selections.shp'))

    for region_zip in glob.glob(os.path.join(SHAPE_DIR, '*-boundary.zip')):
        region_name = os.path.splitext(os.path.basename(region_zip))[0]
        boundary_gdf = gpd.read_file("zip:///" + os.path.join(region_zip, region_name + '.shp'))
        if gjson_gdf.intersects(boundary_gdf)[0]:
            return JsonResponse({'region': region_name})
    return JsonResponse({'error': 'unable to find a region'}), 422


@login_required()
def geoprocess_hydroviewer_clip(request):
    project = request.GET.get('project', False)
    region_name = request.GET.get('region', False)
    if not project:
        return JsonResponse({'error': 'unable to find the project'})
    proj_dir = get_project_directory(project)

    catch_folder = os.path.join(proj_dir, 'selected_catchment')
    dl_folder = os.path.join(proj_dir, 'selected_drainageline')

    if request.GET.get('shapefile', False) == 'drainageline':
        if os.path.exists(dl_folder):
            shutil.rmtree(dl_folder)
        os.mkdir(dl_folder)

        gjson_gdf = gpd.read_file(os.path.join(proj_dir, 'projected_selections', 'projected_selections.shp'))
        dl_name = region_name.replace('boundary', 'drainageline')
        dl_path = os.path.join(SHAPE_DIR, dl_name + '.zip', dl_name + '.shp')
        dl_gdf = gpd.read_file("zip:///" + dl_path)

        dl_point = dl_gdf.representative_point()
        dl_point_clip = gpd.clip(dl_point, gjson_gdf)
        dl_boo_list = dl_point_clip.within(dl_gdf)
        dl_select = dl_gdf[dl_boo_list]
        dl_select.to_file(os.path.join(dl_folder, 'drainageline_select.shp'))
        return JsonResponse({'status': 'success'})

    elif request.GET.get('shapefile', False) == 'catchment':
        if os.path.exists(catch_folder):
            shutil.rmtree(catch_folder)
        os.mkdir(catch_folder)

        dl_select = gpd.read_file(os.path.join(dl_folder, 'drainageline_select.shp'))
        catch_name = region_name.replace('boundary', 'catchment')
        catch_path = os.path.join(SHAPE_DIR, catch_name + '.zip', catch_name + '.shp')
        catch_gdf = gpd.read_file("zip:///" + catch_path)
        catch_gdf = catch_gdf.loc[catch_gdf['COMID'].isin(dl_select['COMID'].to_list())]
        catch_gdf.to_file(os.path.join(catch_folder, 'catchment_select.shp'))
        return JsonResponse({'status': 'success'})

    else:
        raise ValueError('illegal shapefile type specified')
