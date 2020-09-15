let latlonMarker;
let REACHID;

function getBiasCorrectedPlots(gauge_metadata) {
    let data;
    if (gauge_metadata !== false) {
        data = gauge_metadata;
        data['gauge_network'] = $("#gauge_networks").val();
    } else if (!REACHID) {
        alert('No reach-id found');
        return
    } else {
        let csv = $("#uploaded_observations").val();
        data = {
            reach_id: REACHID,
            observation: csv
        }
        if (!confirm('You are about to perform bias correction on reach_id "' + String(REACHID) + '" with uploaded ' +
            'observed steamflow file "' + csv + '". Are you sure you want to continue?')) {
            return
        }
    }
    updateStatusIcons('load');
    updateDownloadLinks('clear');
    $("#chart_modal").modal('show');
    $("#bias_correction_tab_link").show()
    $.ajax({
        type: 'GET',
        async: true,
        data: data,
        url: URL_correct_bias,
        success: function (html) {
            // forecast tab
            $("#forecast_tab_link").tab('show');
            $("#corrected-forecast-chart").append(html['correct_hydro']);
            // historical tab
            $("#historical_tab_link").tab('show');
            $("#historical-chart").html(html['new_hist']);
            $("#historical-table").html('')
            // average flows tab
            $("#avg_flow_tab_link").tab('show');
            $("#daily-avg-chart").html(html['day_avg'])
            $("#monthly-avg-chart").html(html['month_avg'])
            // flow duration curve
            $("#flow_duration_tab_link").tab('show');
            $("#flowduration-chart").html(html['flowdur_plot']);
            // stats tab
            $("#bias_correction_tab_link").tab('show');
            $("#stats_table").html(html['stats_table'])
            $("#volume_plot").html(html['volume_plot']);
            $("#scatters").html(html['scatters']);
            updateStatusIcons('ready');
            updateDownloadLinks('set');
        },
        error: function () {
            updateStatusIcons('fail');
        }
    })
}

function updateStatusIcons(type) {
    let statusObj = $("#request-status");
    if (type === 'identify') {
        statusObj.html(' (Getting stream ID)');
        statusObj.css('color', 'orange');
    } else if (type === 'load') {
        statusObj.html(' (Loading ID ' + REACHID + ')');
        statusObj.css('color', 'orange');
    } else if (type === 'ready') {
        statusObj.html(' (Ready)');
        statusObj.css('color', 'green');
    } else if (type === 'fail') {
        statusObj.html(' (Failed)');
        statusObj.css('color', 'red');
    } else if (type === 'cleared') {
        statusObj.html(' (Cleared)');
        statusObj.css('color', 'grey');
    }
}

function updateDownloadLinks(type) {
    if (type === 'clear') {
        $("#download-forecast-btn").attr('href', '');
        $("#download-historical-btn").attr('href', '');
        $("#download-seasonal-btn").attr('href', '');
    } else if (type === 'set') {
        $("#download-forecast-btn").attr('href', endpoint + 'ForecastStats/?reach_id=' + REACHID);
        $("#download-records-btn").attr('href', endpoint + 'ForecastRecords/?reach_id=' + REACHID);
        $("#download-historical-btn").attr('href', endpoint + 'HistoricSimulation/?reach_id=' + REACHID);
        $("#download-seasonal-btn").attr('href', endpoint + 'SeasonalAverage/?reach_id=' + REACHID);
    }
}

let gaugeNetwork = L.geoJSON(false, {
    onEachFeature: function (feature, layer) {
        layer.on('click', function (event) {L.DomEvent.stopPropagation(event);getBiasCorrectedPlots(feature.properties)});
    },
    pointToLayer: function (feature, latlng) {
        return L.circleMarker(latlng, {radius: 6, fillColor: "#ff0000", color: "#000000", weight: 1, opacity: 1, fillOpacity: 1});
    }
});
let VIIRSlayer = L.tileLayer('https://floods.ssec.wisc.edu/tiles/RIVER-FLDglobal-composite/{z}/{x}/{y}.png', {layers: 'RIVER-FLDglobal-composite: Latest', crossOrigin: true, pane: 'viirs',});

function findReachID() {
    $.ajax({
        type: 'GET',
        async: true,
        url: URL_find_reach_id + L.Util.getParamString({reach_id: $("#search_reachid_input").val()}),
        success: function (response) {
            if (reachMarker) {mapObj.removeLayer(reachMarker)}
            reachMarker = L.marker(L.latLng(response['lat'], response['lon'])).addTo(mapObj);
            mapObj.flyTo(L.latLng(response['lat'], response['lon']), 9);

        },
        error: function () {alert('Unable to find the reach_id specified')}
    })
}
function findLatLon() {
    if (latlonMarker) {mapObj.removeLayer(latlonMarker)}
    let ll = $("#search_latlon_input").val().replace(' ', '').split(',')
    latlonMarker = L.marker(L.latLng(ll[0], ll[1])).addTo(mapObj);
    mapObj.flyTo(L.latLng(ll[0], ll[1]), 9);
}
////////////////////////////////////////////////////////////////////////  GAUGE NETWORKS STUFF
function getGaugeGeoJSON() {
    gaugeNetwork.clearLayers();
    let network = $("#gauge_networks").val();
    if (network === '') {return}
    $.ajax({
        type: 'GET',
        async: true,
        url: URL_get_gauge_geojson + L.Util.getParamString({network: network}),
        success: function (geojson) {gaugeNetwork.addData(geojson).addTo(mapObj);mapObj.flyToBounds(gaugeNetwork.getBounds());},
        error: function () {alert('Error retrieving the locations of the gauge network')}
    })
}
$("#gauge_networks").change(function () {getGaugeGeoJSON()})
////////////////////////////////////////////////////////////////////////  UPLOAD OBSERVATIONAL DATA
$("#hydrograph-csv-form").on('submit', function (e) {
    e.preventDefault();
    let upload_stats = $("#hydrograph-csv-status");
    upload_stats.html('in progress...')
    $.ajax({
        type: 'POST',
        url: URL_upload_new_observations,
        data: new FormData(this),
        dataType: 'json',
        contentType: false,
        cache: false,
        processData: false,
        success: function (response) {
            upload_stats.html('uploaded finished successfully.')
            let uploaded_input = $("#uploaded_observations");
            uploaded_input.empty();
            let new_file_list = response['new_file_list'];
            for (let i = 0; i < new_file_list.length; i++) {
                uploaded_input.append('<option value="'+new_file_list[i][1]+'">'+new_file_list[i][0]+'</option>')
            }
        },
        error: function (response) {
            upload_stats.html('failed to upload. ' + response['error'])
        },
    });
});
$("#start-bias-correction-btn").click(function (e) {getBiasCorrectedPlots(false)})