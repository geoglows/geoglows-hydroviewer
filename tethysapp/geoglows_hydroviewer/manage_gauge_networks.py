import datetime
import glob
import json
import os
from io import StringIO

import pandas as pd
import requests
import xmltodict

from .app import GeoglowsHydroviewer as App


def list_gauge_networks(app_workspace):
    workspace_path = app_workspace.path
    gauge_jsons = glob.glob(os.path.join(workspace_path, 'gauge_networks', '*.json'))
    list_of_gauges = []
    for uploaded_observation in gauge_jsons:
        file_name = os.path.basename(uploaded_observation)
        presentation_name = file_name.replace('_', ' ').replace('.json', '')
        list_of_gauges.append((presentation_name, file_name))
    return tuple([('Choose A Gauge Network', ''), ] + sorted(list_of_gauges))


def get_observed_station_flow(network: str, gauge_metadata: dict):
    if network == 'Colombia_(IDEAM).json':
        # get the gauged data
        url = f'https://www.hydroshare.org/resource/d222676fbd984a81911761ca1ba936bf/' \
              f'data/contents/Discharge_Data/{gauge_metadata["ID"]}.csv'
        df = pd.read_csv(StringIO(requests.get(url).text), index_col=0)
        df.index = pd.to_datetime(df.index).tz_localize('UTC')
    elif network == 'Australia.json':
        # get the gauged data
        now = datetime.datetime.now()
        url = f'http://www.bom.gov.au/waterdata/services?service=kisters&type=queryServices&request=' \
              f'getTimeseriesValues&datasource=0&format=dajson&ts_id={gauge_metadata["ts_id"]}&from=' \
              f'1900-01-01T00:00:00.000%2B09:30&to={now.year}-{now.month}-{now.day}T00:00:00.000%2B09:30&' \
              f'metadata=true&useprecision=false&timezone=GMT%2B09:30&md_returnfields=ts_id,ts_precision&userId=pub'
        f = requests.get(url)

        url = 'http://www.bom.gov.au/water/hrs/content/data/{0}/{0}_daily_ts.csv'.format(gauge_metadata['ID'])
        s = requests.get(url).content

        if f.status_code != 200:
            raise LookupError('Unable to retrieve Australia Gauge Data')
        data = f.json()
        data = data[0]
        data = json.dumps(data)
        data = json.loads(data)
        data = (data.get('data'))

        datesObservedDischarge = [row[0] for row in data]
        observedDischarge = [row[1] for row in data]

        dates = []
        discharge = []

        for i in range(0, len(datesObservedDischarge) - 1):
            year = int(datesObservedDischarge[i][0:4])
            month = int(datesObservedDischarge[i][5:7])
            day = int(datesObservedDischarge[i][8:10])
            hh = int(datesObservedDischarge[i][11:13])
            mm = int(datesObservedDischarge[i][14:16])
            dates.append(datetime.datetime(year, month, day, hh, mm))
            discharge.append(observedDischarge[i])

        datesObservedDischarge = dates
        observedDischarge = discharge

        # convert request into pandas DF
        pairs = [list(a) for a in zip(datesObservedDischarge, observedDischarge)]
        df1 = pd.DataFrame(pairs, columns=['Datetime', 'Observed (m3/s)'])
        df1.set_index('Datetime', inplace=True)

        df1 = df1.groupby(df1.index.strftime("%Y/%m/%d")).mean()
        df1.index = pd.to_datetime(df1.index)

        # Read csv files

        df = pd.read_csv(StringIO(s.decode('utf-8')), index_col=0, skiprows=26)
        df.index = pd.to_datetime(df.index)

        datesDischarge = df.index.tolist()
        dataDischarge = df.iloc[:, 0].values
        dataDischarge.tolist()

        datas = []
        # The given units are in ML/day*(1000m3/1ML)*(1day/86400s). We need to convert to m3/s

        for data in dataDischarge:
            data = 0.01157407407 * data
            # data = str(data)
            datas.append(data)

        dataDischarge = datas

        if isinstance(dataDischarge[0], str):
            dataDischarge = map(float, dataDischarge)

        pairs = [list(a) for a in zip(datesDischarge, dataDischarge)]
        df2 = pd.DataFrame(pairs, columns=['Datetime', 'Observed (m3/s)'])
        df2.set_index('Datetime', inplace=True)

        df = df1.fillna(df2)

        df = df.groupby(df.index.strftime("%Y/%m/%d")).mean()
        df.index = pd.to_datetime(df.index).tz_localize('UTC')

        # Removing Negative Values
        df[df < 0] = 0
    elif network == 'Dominican_Republic_(INDRHI).json':
        url = f'http://128.187.106.131/app/index.php/dr/services/cuahsi_1_1.asmx/GetValuesObject?' \
              f'location={gauge_metadata["ID"]}&variable=Q&startDate=1900-01-01&endDate=2019-12-31&version=1.1'

        r = requests.get(url, verify=False)
        c = xmltodict.parse(r.content)

        y = []
        x = []

        for i in c['timeSeriesResponse']['timeSeries']['values']['value']:
            y.append(float((i['#text'])))
            x.append(datetime.datetime.strptime((i['@dateTime']), "%Y-%m-%dT%H:%M:%S"))

        df = pd.DataFrame(data=y, index=x, columns=['Streamflow'])
        df.index = pd.to_datetime(df.index).tz_localize('UTC')
    elif network == 'West_Africa.json':
        url = f'https://www.hydroshare.org/resource/19ab54be1c9b40669a86076321552f07/data/contents/' \
              f'{gauge_metadata["ID"]}_{gauge_metadata["Station"]}.csv'
        df = pd.read_csv(StringIO(requests.get(url, verify=False).text), index_col=0)
        df.index = pd.to_datetime(df.index).tz_localize('UTC')
    else:
        raise ValueError('Unrecognized Gauge Network Name')

    # build the plot header information
    titles = {'Reach ID': gauge_metadata['GEOGLOWSID'], 'Station Data': network}
    titles_bc = titles
    titles_bc['bias_corrected'] = True

    return df, titles, titles_bc
