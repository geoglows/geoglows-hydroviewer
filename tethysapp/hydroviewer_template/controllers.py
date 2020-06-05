import os
import json

import geoglows.bias as gbc
import geoglows.plots as gpp
import geoglows.streamflow as gsf
import hydrostats.data
import pandas as pd
from django.http import JsonResponse
from django.shortcuts import render
from tethys_sdk.gizmos import SelectInput, Button

from .app import HydroviewerTemplate as App
from .manage_gauge_networks import list_gauge_networks, get_observed_station_flow
from .manage_uploaded_observations import delete_old_observations, list_uploaded_observations

GLOBAL_DELINEATIONS = (
    ('Islands', 'islands-geoglows', 'e3910292be5e4fd79597c6c91cb084cf'),
    ('Australia', 'australia-geoglows', '9572eb7fa8744807962b9268593bd4ad'),
    ('Japan', 'japan-geoglows', 'df5f3e52c51b419d8ee143b919a449b3'),
    ('East Asia', 'east_asia-geoglows', '85ac5bf29cff4aa48a08b8aaeb8e3023'),
    ('South Asia', 'south_asia-geoglows', 'e8f2896be57643eb91220351b961b494'),
    ('Central Asia', 'central_asia-geoglows', '383bc50a88ae4711a8d834a322ced2d5'),
    ('West Asia', 'west_asia-geoglows', 'b62087b814804242a1005368d0ba1b82'),
    ('Middle East', 'middle_east-geoglows', '6de72e805b34488ab1742dae64202a29'),
    ('Europe', 'europe-geoglows', 'c14e1644a94744d8b3204a5be91acaed'),
    ('Africa', 'africa-geoglows', '121bbce392a841178476001843e7510b'),
    ('South America', 'south_america-geoglows', '94f7e730ea034706ae3497a75c764239'),
    ('Central America', 'central_america-geoglows', '36fae4f0e04d40ccb08a8dd1df88365e'),
    ('North America', 'north_america-geoglows', '43ae93136e10439fbf2530e02156caf0'),
)


def home(request):
    """
    Controller for the app home page.
    """
    delete_old_observations()

    uploaded_observations = SelectInput(
        display_text='Uploaded Observational Data',
        name='watersheds_select_input',
        multiple=False,
        original=True,
        options=list_uploaded_observations(),
    )
    gauge_networks = SelectInput(
        display_text='Stream Gauge Networks',
        name='gauge_networks',
        multiple=False,
        original=True,
        options=list_gauge_networks(),
    )
    upload_new_observation = Button(
        name='Upload New Observation',
        display_text='Upload New Observation',
    )

    context = {
        # constants
        'app_url': App.root_url,
        'endpoint': gsf.ENDPOINT,

        # uploaded data
        'uploaded_observations': uploaded_observations,
        'upload_new_observation': upload_new_observation,

        # shapefile/wms custom settings    Used in {% block scripts %}
        'gs_url': 'https://geoserver.hydroshare.org/geoserver/wms',
        'boundary_layer': 'none',
        'catchment_layer': 'HS-94f7e730ea034706ae3497a75c764239:south_america-geoglows-catchment south_america-geoglows-catchment',
        'drainage_layer': 'HS-94f7e730ea034706ae3497a75c764239:south_america-geoglows-drainageline south_america-geoglows-drainageline',

        # appearance customizations
        'branded_name': 'Development',  # {% block app_title %}

        # gauge_networks
        'gauge_networks': gauge_networks,
    }

    return render(request, 'hydroviewer_template/home.html', context)


def get_streamflow(request):
    data = request.GET
    da = data['drain_area']
    reach_id = data['reach_id']
    stats = gsf.forecast_stats(reach_id)
    rec = gsf.forecast_records(reach_id)
    ens = gsf.forecast_ensembles(reach_id)
    hist = gsf.historic_simulation(reach_id)
    rper = gsf.return_periods(reach_id)
    dayavg = hydrostats.data.daily_average(hist, rolling=True)
    monavg = hydrostats.data.monthly_average(hist)
    title_headers = {'Reach ID': reach_id, 'Drainage Area': da}
    return JsonResponse(dict(
        fp=gpp.hydroviewer(rec, stats, ens, rper, titles=title_headers, outformat='plotly_html'),
        hp=gpp.historic_simulation(hist, rper, titles=title_headers, outformat='plotly_html'),
        dp=gpp.daily_averages(dayavg, titles=title_headers, outformat='plotly_html'),
        mp=gpp.monthly_averages(monavg, titles=title_headers, outformat='plotly_html'),
        fdp=gpp.flow_duration_curve(hist, titles=title_headers, outformat='plotly_html'),
        prob_table=gpp.probabilities_table(stats, ens, rper),
        rp_table=gpp.return_periods_table(rper),
    ))


def correct_bias(request):
    # accept the parameters from the user
    data = request.GET.dict()
    network = data.get('gauge_network', False)
    if network:
        reach_id = data['GEOGLOWSID']
        obs_data, titles, titles_bc = get_observed_station_flow(network, data)
    else:
        reach_id = data['reach_id']
        csv = data['observation']
        workspace_path = App.get_app_workspace().path
        obs_path = os.path.join(workspace_path, csv)
        obs_data = pd.read_csv(obs_path, index_col=0)
        obs_data.index = pd.to_datetime(obs_data.index).tz_localize('UTC')
        titles = {'Reach ID': reach_id, 'Station Data': csv}
        titles_bc = {'Reach ID': reach_id, 'Station Data': csv, 'bias_corrected': True}

    # get the data you need to correct bias
    sim_data = gsf.historic_simulation(reach_id)
    forecast_stats = gsf.forecast_stats(reach_id)
    forecast_rec = gsf.forecast_records(reach_id)
    forecast_ens = gsf.forecast_ensembles(reach_id)

    # corrected data
    fixed_hist = gbc.correct_historical(sim_data, obs_data)
    fixed_stats = gbc.correct_forecast(forecast_stats, sim_data, obs_data)
    fixed_rec = gbc.correct_forecast(forecast_rec, sim_data, obs_data, use_month=-1)
    fixed_ens = gbc.correct_forecast(forecast_ens, sim_data, obs_data)

    return JsonResponse(dict(
        new_hist=gpp.corrected_historical(
            fixed_hist, sim_data, obs_data, titles=titles_bc, outformat='plotly_html'),
        day_avg=gpp.corrected_day_average(
            fixed_hist, sim_data, obs_data, titles=titles_bc, outformat='plotly_html'),
        month_avg=gpp.corrected_month_average(
            fixed_hist, sim_data, obs_data, titles=titles_bc, outformat='plotly_html'),
        correct_hydro=gpp.hydroviewer(
            fixed_rec, fixed_stats, fixed_ens, titles=titles_bc, outformat='plotly_html'),
        volume_plot=gpp.corrected_volume_compare(
            fixed_hist, sim_data, obs_data, titles=titles_bc, outformat='plotly_html'),
        flowdur_plot=gpp.flow_duration_curve(fixed_hist, titles=titles_bc, outformat='plotly_html'),
        scatters=gpp.corrected_scatterplots(fixed_hist, sim_data, obs_data, titles=titles, outformat='plotly_html'),
        stats_table=gbc.statistics_tables(fixed_hist, sim_data, obs_data),
    ))


def find_reach_id(request):
    reach_id = request.GET['reach_id']
    lat, lon = gsf.reach_to_latlon(int(reach_id))
    return JsonResponse({'lat': lat, 'lon': lon})


def get_gauge_geojson(request):
    workspace_path = App.get_app_workspace().path
    with open(os.path.join(workspace_path, 'gauge_networks', request.GET['network'])) as geojson:
        return JsonResponse(json.load(geojson))
