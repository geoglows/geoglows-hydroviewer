import os
import glob
import datetime
from .app import HydroviewerTemplate as App
from django.http import JsonResponse


def delete_old_observations():
    workspace_path = App.get_app_workspace().path
    uploaded_observations = glob.glob(os.path.join(workspace_path, '*.csv'))
    expiration_time = datetime.datetime.now() - datetime.timedelta(days=1)
    for uploaded_observation in uploaded_observations:
        created_date = datetime.datetime.fromtimestamp(os.path.getctime(uploaded_observation))
        if created_date <= expiration_time:
            os.remove(uploaded_observation)
    return


def list_uploaded_observations():
    workspace_path = App.get_app_workspace().path
    uploaded_observations = glob.glob(os.path.join(workspace_path, '*.csv'))
    list_of_observations = []
    for uploaded_observation in uploaded_observations:
        file_name = os.path.basename(uploaded_observation)
        presentation_name = file_name.replace('_', ' ').replace('.csv', '')
        list_of_observations.append((presentation_name, file_name))
    return tuple(sorted(list_of_observations))


def upload_new_observations(request):
    print(request.POST)
    print(request.FILES)
    files = request.FILES.getlist('files')
    print(files)
    workspace_path = App.get_app_workspace().path

    # write the new files to the directory
    for n, file in enumerate(files):
        with open(os.path.join(workspace_path, file.name), 'wb') as dst:
            for chunk in files[n].chunks():
                dst.write(chunk)
    return JsonResponse(dict(new_file_list=list_uploaded_observations()))
