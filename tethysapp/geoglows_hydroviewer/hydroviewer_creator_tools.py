import glob
import os

from .app import GeoglowsHydroviewer as App

SHAPE_DIR = App.get_custom_setting('global_delineation_shapefiles_directory')


def get_project_directory(project):
    workspace_path = App.get_app_workspace().path
    project = str(project).replace(' ', '_')
    return os.path.join(workspace_path, 'projects', project)


def shapefiles_downloaded():
    shape_dir_contents = glob.glob(os.path.join(SHAPE_DIR, '*geoglows*.zip'))
    if len(shape_dir_contents) == 39:
        return True
    return False
