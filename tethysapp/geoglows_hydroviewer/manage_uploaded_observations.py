import datetime
import glob
import os

import pandas as pd
from django.http import JsonResponse

from tethys_sdk.routing import controller


@controller(name='upload_new_observations', url='hydroviewer/upload_new_observations', app_workspace=True)
def upload_new_observations(request, app_workspace):
    delete_old_observations(app_workspace)
    workspace_path = app_workspace.path
    files = request.FILES
    for file in files:
        new_observation_path = os.path.join(workspace_path, 'observations', files[file].name)
        with open(new_observation_path, 'wb') as dst:
            for chunk in files[file].chunks():
                dst.write(chunk)
        try:
            df = pd.read_csv(new_observation_path, index_col=0)
            df.dropna(inplace=True)
        except Exception as e:
            JsonResponse(dict(error='Cannot read the csv provided. It may not be a valid csv file.'))
        try:
            df.index = pd.to_datetime(df.index)
            df = df.resample('D', axis=0).mean()
        except Exception as e:
            JsonResponse(dict(error='Unable to recognize dates. Please specify 1 date/streamflow value pair per date. '
                                    'Recommended datetime format is YYYY-MM-DD HH:MM:SS'))
        try:
            df.index = pd.to_datetime(df.index).tz_localize('UTC')
        except Exception as e:
            pass

        df.to_csv(new_observation_path)

    return JsonResponse(dict(new_file_list=list_uploaded_observations(app_workspace)))


def delete_old_observations(app_workspace):
    workspace_path = app_workspace.path
    uploaded_observations = glob.glob(os.path.join(workspace_path, 'observations', '*.csv'))
    expiration_time = datetime.datetime.now() - datetime.timedelta(days=1)
    for uploaded_observation in uploaded_observations:
        created_date = datetime.datetime.fromtimestamp(os.path.getctime(uploaded_observation))
        if created_date <= expiration_time:
            os.remove(uploaded_observation)
    return


def list_uploaded_observations(app_workspace):
    workspace_path = app_workspace.path
    uploaded_observations = glob.glob(os.path.join(workspace_path, 'observations', '*.csv'))
    list_of_observations = []
    for uploaded_observation in uploaded_observations:
        file_name = os.path.basename(uploaded_observation)
        presentation_name = file_name.replace('_', ' ').replace('.csv', '')
        list_of_observations.append((presentation_name, file_name))
    return tuple(sorted(list_of_observations))
