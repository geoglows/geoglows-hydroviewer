import glob
import os
import shutil
from zipfile import ZipFile

import geopandas as gpd
from django.http import JsonResponse
from tethys_sdk.permissions import login_required
from tethys_sdk.routing import controller

from .app import GeoglowsHydroviewer as App
from .hydroviewer_creator_tools import get_project_directory

SHAPE_DIR = App.get_custom_setting('global_delineation_shapefiles_directory')


@controller(name='geoprocess_idregion', url='creator/project/geoprocessing/geoprocess_idregion', app_workspace=True)
def geoprocess_hydroviewer_idregion(request, app_workspace):
    project = request.GET.get('project', False)
    if not project:
        raise FileNotFoundError('project directory not found')
    proj_dir = get_project_directory(project, app_workspace)
    gjson_gdf = gpd.read_file(os.path.join(proj_dir, 'boundaries.json'))
    gjson_gdf = gjson_gdf.to_crs(epsg=3857)

    for region_zip in glob.glob(os.path.join(SHAPE_DIR, '*-boundary.zip')):
        region_name = os.path.splitext(os.path.basename(region_zip))[0]
        boundary_gdf = gpd.read_file("zip:///" + os.path.join(region_zip, region_name + '.shp'))
        if gjson_gdf.intersects(boundary_gdf)[0]:
            return JsonResponse({'region': region_name})
    return JsonResponse({'error': 'unable to find a region'}), 422


@controller(name='geoprocess_clip', url='creator/project/geoprocessing/geoprocess_clip', app_workspace=True, )
def geoprocess_hydroviewer_clip(request, app_workspace):
    project = request.GET.get('project', False)
    region_name = request.GET.get('region', False)
    if not project:
        return JsonResponse({'error': 'unable to find the project'})
    proj_dir = get_project_directory(project, app_workspace)

    catch_folder = os.path.join(proj_dir, 'catchment_shapefile')
    dl_folder = os.path.join(proj_dir, 'drainageline_shapefile')
    project = str.lower(project)

    if request.GET.get('shapefile', False) == 'drainageline':
        if os.path.exists(dl_folder):
            shutil.rmtree(dl_folder)
        os.mkdir(dl_folder)

        gjson_gdf = gpd.read_file(os.path.join(proj_dir, 'boundaries.json'))
        gjson_gdf = gjson_gdf.to_crs(epsg=3857)
        dl_name = region_name.replace('boundary', 'drainageline')
        dl_path = os.path.join(SHAPE_DIR, dl_name + '.zip', dl_name + '.shp')
        dl_gdf = gpd.read_file("zip:///" + dl_path)

        dl_point = dl_gdf.representative_point()
        dl_point_clip = gpd.clip(dl_point, gjson_gdf)
        dl_boo_list = dl_point_clip.within(dl_gdf)
        dl_select = dl_gdf[dl_boo_list]
        dl_select.to_file(os.path.join(dl_folder, project + '_drainagelines.shp'))
        return JsonResponse({'status': 'success'})

    elif request.GET.get('shapefile', False) == 'catchment':
        if os.path.exists(catch_folder):
            shutil.rmtree(catch_folder)
        os.mkdir(catch_folder)

        dl_select = gpd.read_file(os.path.join(dl_folder, project + '_drainagelines.shp'))
        catch_name = region_name.replace('boundary', 'catchment')
        catch_path = os.path.join(SHAPE_DIR, catch_name + '.zip', catch_name + '.shp')
        catch_gdf = gpd.read_file("zip:///" + catch_path)
        catch_gdf = catch_gdf.loc[catch_gdf['COMID'].isin(dl_select['COMID'].to_list())]
        catch_gdf.to_file(os.path.join(catch_folder, project + '_catchments.shp'))
        return JsonResponse({'status': 'success'})

    else:
        raise ValueError('illegal shapefile type specified')


@controller(name='geoprocess_zipexport', url='/creator/project/geoprocessing/geoprocess_zip_shapefiles',
            app_workspace=True)
def geoprocess_zip_shapefiles(request, app_workspace):
    project = request.GET.get('project', False)
    proj_dir = get_project_directory(project, app_workspace)

    catchment_zip = os.path.join(proj_dir, 'catchment_shapefile.zip')
    drainageline_zip = os.path.join(proj_dir, 'drainageline_shapefile.zip')
    project = str.lower(project)
    try:
        with ZipFile(catchment_zip, 'w') as zipped:
            for component in glob.glob(os.path.join(proj_dir, 'catchment_shapefile', project + '_catchments.*')):
                zipped.write(component, arcname=os.path.basename(component))
        shutil.rmtree(os.path.join(proj_dir, 'catchment_shapefile'))

        with ZipFile(drainageline_zip, 'w') as zipped:
            for component in glob.glob(os.path.join(proj_dir, 'drainageline_shapefile', project + '_drainagelines.*')):
                zipped.write(component, arcname=os.path.basename(component))
            shutil.rmtree(os.path.join(proj_dir, 'drainageline_shapefile'))

        return JsonResponse({'status': 'success'})

    except FileNotFoundError as e:
        if os.path.isdir(os.path.join(proj_dir, 'drainageline_shapefile')):
            shutil.rmtree(os.path.join(proj_dir, 'drainageline_shapefile'))
        if os.path.isdir(os.path.join(proj_dir, 'catchment_shapefile')):
            shutil.rmtree(os.path.join(proj_dir, 'catchment_shapefile'))
        if os.path.exists(catchment_zip):
            os.remove(catchment_zip)
        if os.path.exists(drainageline_zip):
            os.remove(drainageline_zip)
        raise e

    except Exception as e:
        raise e
