////////////////////////////////////////////////////////////////////////  SETUP THE MAP
let reachid;
let marker = null;
const mapObj = L.map('map', {
        zoom: 3,
        minZoom: 2,
        boxZoom: true,
        maxBounds: L.latLngBounds(L.latLng(-100, -225), L.latLng(100, 225)),
        center: [20, 0],
    });
// add basemaps
const basemapsJson = {
    "ESRI Topographic": L.esri.basemapLayer('Topographic').addTo(mapObj),
    "ESRI Terrain": L.layerGroup([L.esri.basemapLayer('Terrain'), L.esri.basemapLayer('TerrainLabels')]),
    "ESRI Grey": L.esri.basemapLayer('Gray'),
}
// create map panes which help sort layer drawing order
mapObj.createPane('watershedlayers');
mapObj.getPane('watershedlayers').style.zIndex = 250;
mapObj.createPane('viirs');
mapObj.getPane('viirs').style.zIndex = 200;
// add the legends and latlon box to the map
let legend = L.control({position: 'bottomright'});
legend.onAdd = function () {
    let div = L.DomUtil.create('div', 'legend');
    let start = '<div><svg width="20" height="20" viewPort="0 0 20 20" version="1.1" xmlns="http://www.w3.org/2000/svg">';
    div.innerHTML = '<div class="legend">' +
        start + '<polyline points="19 1, 1 6, 19 14, 1 19" stroke="purple" fill="transparent" stroke-width="2"/></svg> 20-yr Return Period Flow </div>' +
        start + '<polyline points="19 1, 1 6, 19 14, 1 19" stroke="red" fill="transparent" stroke-width="2"/></svg> 10-yr Return Period Flow </div>' +
        start + '<polyline points="19 1, 1 6, 19 14, 1 19" stroke="gold" fill="transparent" stroke-width="2"/></svg> 2-yr Return Period Flow</div>' +
        start + '<polyline points="19 1, 1 6, 19 14, 1 19" stroke="blue" fill="transparent" stroke-width="2"/></svg> Stream Line </div>' +
        '</div>';
    return div
};
legend.addTo(mapObj);
// lat/lon tracking box on the bottom left of the map
let latlon = L.control({position: 'bottomleft'});
latlon.onAdd = function () {
    let div = L.DomUtil.create('div', 'well well-sm');
    div.innerHTML = '<div id="mouse-position" style="text-align: center"></div>';
    return div;
};
latlon.addTo(mapObj);
mapObj.on("mousemove", function (event) {$("#mouse-position").html('Lat: ' + event.latlng.lat.toFixed(5) + ', Lon: ' + event.latlng.lng.toFixed(5));});
mapObj.on("click", function (event) {
    if (mapObj.getZoom()<=8){mapObj.flyTo(event.latlng, 9); return}
    else {mapObj.flyTo(event.latlng)}
    if (marker) {mapObj.removeLayer(marker)}
    marker = L.marker(event.latlng).addTo(mapObj);
    for (let i in chart_divs) {chart_divs[i].html('')}
    updateStatusIcons('load');
    $("#chart_modal").modal('show')
    L.esri.identifyFeatures({
        url: 'https://livefeeds2.arcgis.com/arcgis/rest/services/GEOGLOWS/GlobalWaterModel_Medium/MapServer'
    })
        .on(mapObj).tolerance(30)
        .at([event.latlng['lat'], event.latlng['lng']])
        .run(function (error, featureCollection) {
            if (error) {
                updateStatusIcons('fail');
                alert('Error finding the reach_id')
                return;
            }
            console.log(featureCollection.features[0].properties);
            reachid = featureCollection.features[0].properties["COMID (Stream Identifier)"];
            getStreamflowPlots();
        })
});
////////////////////////////////////////////////////////////////////////  ESRI LAYER ANIMATION CONTROLS
let layerAnimationTime = new Date();
layerAnimationTime = new Date(layerAnimationTime.toISOString())
layerAnimationTime.setUTCHours(0);
layerAnimationTime.setUTCMinutes(0);
layerAnimationTime.setUTCSeconds(0);
layerAnimationTime.setUTCMilliseconds(0);
const currentDate = $("#current-map-date");
const startDateTime = new Date(layerAnimationTime);
const endDateTime = new Date(layerAnimationTime.setUTCHours(5 * 24));
layerAnimationTime = new Date(startDateTime);
currentDate.html(layerAnimationTime);
const slider = $("#time-slider")
slider.change(function () {
    refreshLayerAnimation()
})
function refreshLayerAnimation() {
    layerAnimationTime = new Date(startDateTime);
    layerAnimationTime.setUTCHours(slider.val() * 3);
    currentDate.html(layerAnimationTime);
    globalLayer.setTimeRange(layerAnimationTime, endDateTime);
}
let animate = false;
function playAnimation(once = false) {
    if (!animate) {return}
    if (layerAnimationTime < endDateTime) {
        slider.val(Number(slider.val()) + 1)
    } else {
        slider.val(0)
    }
    refreshLayerAnimation();
    if (once) {
        animate = false;
        return
    }
    setTimeout(playAnimation, 500);
}
$("#animationPlay").click(function () {
    animate = true;
    playAnimation()
})
$("#animationStop").click(function () {
    animate = false;
})
$("#animationPlus1").click(function(){
    animate = true;
    playAnimation(true)
})
$("#animationBack1").click(function(){
    if (layerAnimationTime > startDateTime) {
        slider.val(Number(slider.val()) - 1)
    } else {
        slider.val(40)
    }
    refreshLayerAnimation();
})
////////////////////////////////////////////////////////////////////////  ADD WMS LAYERS FOR DRAINAGE LINES, VIIRS, ETC - SEE HOME.HTML TEMPLATE
let reachMarker;
let latlonMarker;
let gaugeNetwork = L.geoJSON(false, {
    onEachFeature: function (feature, layer) {
        layer.on('click', function (event) {L.DomEvent.stopPropagation(event);getBiasCorrectedPlots(feature.properties)});
    },
    pointToLayer: function (feature, latlng) {
        return L.circleMarker(latlng, {radius: 6, fillColor: "#ff0000", color: "#000000", weight: 1, opacity: 1, fillOpacity: 1});
    }
});
let VIIRSlayer = L.tileLayer('https://floods.ssec.wisc.edu/tiles/RIVER-FLDglobal-composite/{z}/{x}/{y}.png', {layers: 'RIVER-FLDglobal-composite: Latest', crossOrigin: true, pane: 'viirs',});
const globalLayer = L.esri.dynamicMapLayer({
    url: 'https://livefeeds2.arcgis.com/arcgis/rest/services/GEOGLOWS/GlobalWaterModel_Medium/MapServer',
    useCors: false,
    layers: [0],
    from: startDateTime,
    to: endDateTime,
}).addTo(mapObj);
L.control.layers(basemapsJson, {'Stream Network': globalLayer, 'Gauge Network': gaugeNetwork, 'VIIRS Imagery': VIIRSlayer}, {'collapsed': false}).addTo(mapObj);
////////////////////////////////////////////////////////////////////////  GET DATA FROM API AND MANAGING PLOTS
const chart_divs = [$("#forecast-chart"), $("#corrected-forecast-chart"), $("#forecast-table"), $("#historical-chart"), $("#historical-table"), $("#daily-avg-chart"), $("#monthly-avg-chart"), $("#flowduration-chart"), $("#volume_plot"), $("#scatters"), $("#stats_table")];
function getStreamflowPlots() {
    updateStatusIcons('load');
    updateDownloadLinks('clear');
    for (let i in chart_divs) {chart_divs[i].html('')}  // clear the contents of old chart divs
    let ftl = $("#forecast_tab_link");  // select divs with jquery so we can reuse them
    let fc = chart_divs[0];
    ftl.tab('show')
    fc.html('<img src="https://www.ashland.edu/sites/all/themes/ashlandecard/2014card/images/load.gif">');
    fc.css('text-align', 'center');
    $.ajax({
        type: 'GET',
        async: true,
        data: {reach_id: reachid},
        url: URL_get_streamflow,
        success: function (html) {
            // forecast tab
            ftl.tab('show');
            fc.html(html['fp']);
            $("#forecast-table").html(html['prob_table']);
            // historical tab
            $("#historical_tab_link").tab('show');
            $("#historical-chart").html(html['hp']);
            $("#historical-table").html(html['rp_table']);
            // average flows tab
            $("#avg_flow_tab_link").tab('show');
            $("#daily-avg-chart").html(html['dp']);
            $("#monthly-avg-chart").html(html['mp']);
            // $("#monthly-avg-chart").html(html['sp']);
            // flow duration tab
            $("#flow_duration_tab_link").tab('show');
            $("#flowduration-chart").html(html['fdp']);
            // update other messages and links
            ftl.tab('show');
            updateStatusIcons('ready');
            updateDownloadLinks('set');
            $("#bias_correction_tab_link").show()
        },
        error: function () {
            updateStatusIcons('fail');
            $("#bias_correction_tab_link").hide()
            for (let i in chart_divs) {
                chart_divs[i].html('')
            }
        }
    })
}
function getBiasCorrectedPlots(gauge_metadata) {
    let data;
    if (gauge_metadata !== false) {
        data = gauge_metadata;
        data['gauge_network'] = $("#gauge_networks").val();
    } else if (!reachid) {
        alert('No reach-id found');
        return
    } else {
        let csv = $("#uploaded_observations").val();
        data = {
            reach_id: reachid,
            observation: csv
        }
        if (!confirm('You are about to perform bias correction on reach_id "' + String(reachid) + '" with uploaded ' +
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
    if (type === 'load') {
        statusObj.html(' (loading)');
        statusObj.css('color', 'orange');
    } else if (type === 'ready') {
        statusObj.html(' (ready)');
        statusObj.css('color', 'green');
    } else if (type === 'fail') {
        statusObj.html(' (failed)');
        statusObj.css('color', 'red');
    } else if (type === 'cleared') {
        statusObj.html(' (cleared)');
        statusObj.css('color', 'grey');
    }
}
function updateDownloadLinks(type) {
    if (type === 'clear') {
        $("#download-forecast-btn").attr('href', '');
        $("#download-historical-btn").attr('href', '');
        $("#download-seasonal-btn").attr('href', '');
    } else if (type === 'set') {
        $("#download-forecast-btn").attr('href', endpoint + 'ForecastStats/?reach_id=' + reachid);
        $("#download-records-btn").attr('href', endpoint + 'ForecastRecords/?reach_id=' + reachid);
        $("#download-historical-btn").attr('href', endpoint + 'HistoricSimulation/?reach_id=' + reachid);
        $("#download-seasonal-btn").attr('href', endpoint + 'SeasonalAverage/?reach_id=' + reachid);
    }
}
function fix_buttons(tab) {
    let buttons = [$("#download-forecast-btn"), $("#download-historical-btn"), $("#download-averages-btn"), $("#start-bias-correction-btn")]
    for (let i in buttons) {
        buttons[i].hide()
    }
    if (tab === 'forecast') {
        buttons[0].show()
    } else if (tab === 'historical') {
        buttons[1].show()
    } else if (tab === 'averages') {
        buttons[2].show()
    } else if (tab === 'biascorrection') {
        buttons[3].show()
    }
    fix_chart_sizes(tab);
    $("#resize_charts").attr({'onclick': "fix_chart_sizes('" + tab + "')"})
}
function fix_chart_sizes(tab) {
    let divs = [];
    if (tab === 'forecast') {
        divs = [$("#forecast-chart .js-plotly-plot")]
    } else if (tab === 'records') {
        divs = [$("#records-chart .js-plotly-plot")]
    } else if (tab === 'historical') {
        divs = [$("#historical-5-chart .js-plotly-plot")]
    } else if (tab === 'averages') {
        divs = [$("#daily-avg-chart .js-plotly-plot"), $("#monthly-avg-chart .js-plotly-plot")]
    } else if (tab === 'flowduration') {
        divs = [$("#flowduration-5-chart .js-plotly-plot")]
    } else if (tab === 'biascorrection') {
        divs = [$("#volume_plot .js-plotly-plot"), $("#scatters .js-plotly-plot")];
    }
    for (let i in divs) {
        try {
            divs[i].css('height', 500);
            Plotly.Plots.resize(divs[i][0]);
        } catch (e) {
        }
    }
}
$("#forecast_tab_link").on('click', function () {fix_buttons('forecast')})
$("#historical_tab_link").on('click', function () {fix_buttons('historical')})
$("#avg_flow_tab_link").on('click', function () {fix_buttons('averages')})
$("#flow_duration_tab_link").on('click', function () {fix_buttons('flowduration')})
$("#bias_correction_tab_link").on('click', function () {fix_buttons('biascorrection')})
////////////////////////////////////////////////////////////////////////  OTHER UTILITIES ON THE LEFT COLUMN
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
            console.log(response);
        },
        error: function (response) {
            upload_stats.html('failed to upload. ' + response['error'])
        },
    });
});
$("#start-bias-correction-btn").click(function (e) {getBiasCorrectedPlots(false)})