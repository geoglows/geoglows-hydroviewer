import pandas as pd
import geoglows.streamflow as gsf
import geoglows.bias as gbc
import geoglows.plots as gpp
from django.http import JsonResponse
from django.shortcuts import render
import os
from .app import HydroviewerTemplate as App
from .manage_uploaded_observations import delete_old_observations, list_uploaded_observations
from tethys_sdk.gizmos import SelectInput, Button


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

        # shapefile/wms custom settings
        'gs_url': 'https://geoserver.hydroshare.org/geoserver/wms',
        'boundary_layer': 'none',
        'catchment_layer': 'HS-df5f3e52c51b419d8ee143b919a449b3:japan-geoglows-catchment japan-geoglows-catchment',
        'drainage_layer': 'HS-df5f3e52c51b419d8ee143b919a449b3:japan-geoglows-drainageline japan-geoglows-drainageline',

        # appearance customizations
        'branded_name': 'Development',
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
    seas = gsf.seasonal_average(reach_id)
    title_headers = {'Reach ID': reach_id, 'Drainage Area': da}
    return JsonResponse(dict(
        fp=gpp.hydroviewer_plot(rec, stats, ens, rper, title_headers=title_headers, outformat='plotly_html'),
        rcp=gpp.records_plot(rec, rper, outformat='plotly_html'),
        hp=gpp.historical_plot(hist, rper, title_headers=title_headers, outformat='plotly_html'),
        sp=gpp.seasonal_plot(seas, title_headers=title_headers, outformat='plotly_html'),
        fdp=gpp.flow_duration_curve_plot(hist, title_headers=title_headers, outformat='plotly_html'),
        prob_table=gpp.probabilities_table(stats, ens, rper),
        rp_table=gpp.return_periods_table(rper),
    ))


def correct_bias(request):
    # accept the parameters from the user
    data = request.GET
    reach_id = data['reach_id']
    csv = data['observation_name']

    # find their csv
    workspace_path = App.get_app_workspace().path
    obs_path = os.path.join(workspace_path, csv)

    # get the data you need to correct bias
    sim_data = gsf.historic_simulation(reach_id)
    obs_data = pd.read_csv(obs_path)
    forecast_stats = gsf.forecast_stats(reach_id)
    forecast_rec = gsf.forecast_records(reach_id)
    forecast_ens = gsf.forecast_ensembles(reach_id)

    # corrected data
    fixed_hist = gbc.correct_historical_simulation(sim_data, obs_data)
    fixed_stats = gbc.correct_forecast_flows(forecast_stats, sim_data, obs_data)
    fixed_rec = gbc.correct_forecast_flows(forecast_rec, sim_data, obs_data, use_month=-1)
    fixed_ens = gbc.correct_forecast_flows(forecast_ens, sim_data, obs_data)

    # header information
    headers = {'Reach ID': reach_id, 'Station Data': csv}

    return JsonResponse(dict(
        hist_compare_plot=gpp.bias_corrected_historical(
            fixed_hist, sim_data, obs_data, title_headers=headers, outformat='plotly-html'),
        day_avg=gpp.bias_corrected_daily_averages(
            fixed_hist, sim_data, obs_data, title_headers=headers, outformat='plotly-html'),
        month_avg=gpp.bias_corrected_monthly_averages(
            fixed_hist, sim_data, obs_data, title_headers=headers, outformat='plotly-html'),
        correct_hydro=gpp.hydroviewer_plot(
            fixed_rec, fixed_stats, fixed_ens, title_headers=headers, outformat='plotly-html'),
        volume_plot=gpp.bias_corrected_volume_comparison(
            fixed_hist, sim_data, obs_data, title_headers=headers, outformat='plotly-html'),
        stats_table=gbc.make_statistics_tables(fixed_hist, sim_data, obs_data),
    ))
