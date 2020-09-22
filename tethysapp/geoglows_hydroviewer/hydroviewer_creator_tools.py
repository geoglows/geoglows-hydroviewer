import glob
import os
import shutil
from zipfile import ZipFile

from .app import GeoglowsHydroviewer as App

SHAPE_DIR = App.get_custom_setting('global_delineation_shapefiles_directory')


def get_project_directory(project):
    workspace_path = App.get_app_workspace().path
    project = str(project).replace(' ', '_')
    return os.path.join(workspace_path, 'projects', project)


def shapefiles_downloaded():
    shape_dir_contents = glob.glob(os.path.join(SHAPE_DIR, '*.zip'))
    if len(shape_dir_contents) == 39:
        return True
    return False


def zip_project_shapefiles(project):
    proj_dir = get_project_directory(project)
    zip_path = os.path.join(proj_dir, 'hydroviewer_shapefiles.zip')
    catchment_shapefile = os.path.join(proj_dir, 'selected_catchment', 'catchment_select.shp')
    drainageline_shapefile = os.path.join(proj_dir, 'selected_drainageline', 'drainageline_select.shp')
    if not os.path.exists(catchment_shapefile):
        raise FileNotFoundError('selected catchment shapefile does not exist')
    if not os.path.exists(drainageline_shapefile):
        raise FileNotFoundError('selected drainageline shapefile does not exist')
    try:
        with ZipFile(zip_path, 'w') as zipfile:
            catchment_components = glob.glob(os.path.join(proj_dir, 'selected_catchment', 'catchment_select.*'))
            for component in catchment_components:
                zipfile.write(component, arcname=os.path.join('selected_catchment', os.path.basename(component)))
            dl_components = glob.glob(os.path.join(proj_dir, 'selected_drainageline', 'drainageline_select.*'))
            for component in dl_components:
                zipfile.write(component, arcname=os.path.join('selected_drainageline', os.path.basename(component)))
    except Exception as e:
        shutil.rmtree(zip_path)
    return
