import os

from .app import HydroviewerTemplate as App


def get_project_directory(project):
    workspace_path = App.get_app_workspace().path
    project = str(project).replace(' ', '_')
    return os.path.join(workspace_path, 'projects', project)
