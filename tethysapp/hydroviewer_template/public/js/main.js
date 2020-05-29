////////////////////////////////////////////////////////////////////////  WEB MAPPING FEATURE SERVICE EXTENSION
L.TileLayer.WMFS = L.TileLayer.WMS.extend({
    GetFeatureInfo: function (evt) {
        // Construct a GetFeatureInfo request URL given a point
        let size = this._map.getSize();
        let params = {
            request: 'GetFeatureInfo',
            service: 'WMS',
            srs: 'EPSG:4326',
            version: this.wmsParams.version,
            format: this.wmsParams.format,
            bbox: this._map.getBounds().toBBoxString(),
            height: size.y,
            width: size.x,
            layers: this.wmsParams.layers,
            query_layers: this.wmsParams.layers,
            info_format: 'application/json',
            buffer: 18,
        };
        params[params.version === '1.3.0' ? 'i' : 'x'] = evt.containerPoint.x;
        params[params.version === '1.3.0' ? 'j' : 'y'] = evt.containerPoint.y;

        let url = this._url + L.Util.getParamString(params, this._url, true);
        let reachid = null;
        let drain_area = null;

        if (url) {
            $.ajax({
                async: false,
                type: "GET",
                url: url,
                info_format: 'application/json',
                success: function (data) {
                    reachid = data.features[0].properties['COMID'];
                    drain_area = data.features[0].properties['Tot_Drain_'];
                }
            });
        }
        return [reachid, drain_area]
    },
});

L.tileLayer.WMFS = function (url, options) {
    return new L.TileLayer.WMFS(url, options);
};
////////////////////////////////////////////////////////////////////////  MAP FUNCTIONS AND VARIABLES
function hydroviewer() {
    return L.map('map', {
        zoom: 3,
        minZoom: 2,
        boxZoom: true,
        maxBounds: L.latLngBounds(L.latLng(-100, -225), L.latLng(100, 225)),
        center: [20, 0],
    })
}
function basemaps() {
    return {
        "ESRI Topographic": L.esri.basemapLayer('Topographic').addTo(mapObj),
        "ESRI Terrain": L.layerGroup([L.esri.basemapLayer('Terrain'), L.esri.basemapLayer('TerrainLabels')]),
        "ESRI Grey": L.esri.basemapLayer('Gray'),
    }
}
function getWatershedComponent(layername) {
    return L.tileLayer.wms(geoserver_url, {
        version: '1.1.0',
        layers: layername,
        useCache: true,
        crossOrigin: false,
        format: 'image/png',
        transparent: true,
        opacity: 1,
        pane: 'watershedlayers',
    })
}
function getDrainageLine(layername) {
    return L.tileLayer.WMFS(geoserver_url, {
        version: '1.1.0',
        layers: layername,
        useCache: true,
        crossOrigin: false,
        format: 'image/png',
        transparent: true,
        opacity: 1,
        pane: 'watershedlayers',
    })
}
function getVIIRS() {
    return L.tileLayer('https://floods.ssec.wisc.edu/tiles/RIVER-FLDglobal-composite/{z}/{x}/{y}.png', {
        layers: 'RIVER-FLDglobal-composite: Latest',
        crossOrigin: true,
        pane: 'viirs',
    });
}
let reachid;
let drain_area;
let needsRefresh = {};
let marker = null;
////////////////////////////////////////////////////////////////////////  SETUP THE MAP
// make the map
let mapObj = hydroviewer();
// create map panes which help sort layer drawing order
mapObj.createPane('watershedlayers');
mapObj.getPane('watershedlayers').style.zIndex = 250;
mapObj.createPane('viirs');
mapObj.getPane('viirs').style.zIndex = 200;
// get the VIIRS imagery layer
let VIIRSlayer = getVIIRS();
// add basemaps
let basemapObj = basemaps();
// add the legends and latlon box to the map
let legend = L.control({position: 'bottomright'});
legend.onAdd = function () {
    let div = L.DomUtil.create('div', 'legend');
    let start = '<div><svg width="20" height="20" viewPort="0 0 20 20" version="1.1" xmlns="http://www.w3.org/2000/svg">';
    div.innerHTML = '<div class="legend">' +
        start + '<polyline points="19 1, 1 6, 19 14, 1 19" stroke="blue" fill="transparent" stroke-width="2"/></svg>Drainage Line </div>' +
        start + '<polygon points="1 10, 5 3, 13 1, 19 9, 14 19, 9 13" stroke="black" fill="grey" stroke-width="2"/></svg>Watershed Boundary </div>' +
        '</div>';
    return div
};
legend.addTo(mapObj);
let latlon = L.control({position: 'bottomleft'});
latlon.onAdd = function () {
    let div = L.DomUtil.create('div', 'well well-sm');
    div.innerHTML = '<div id="mouse-position" style="text-align: center"></div>';
    return div;
};
latlon.addTo(mapObj);
mapObj.on("mousemove", function (event) {
    $("#mouse-position").html('Lat: ' + event.latlng.lat.toFixed(5) + ', Lon: ' + event.latlng.lng.toFixed(5));
});

// add layers to the map: the boundary, catchment, and drainage layers are the geoserver layer names and determined by the python controller and rendered in the templates
let ctrllayers = {};
if (boundary_layer !== 'none') {boundary_layer = getWatershedComponent(boundary_layer); ctrllayers['Hydroviewer Boundaries'] = boundary_layer}
if (catchment_layer !== 'none') {catchment_layer = getWatershedComponent(catchment_layer); ctrllayers['Watershed Catchments'] = catchment_layer}
drainage_layer = getDrainageLine(drainage_layer).addTo(mapObj);
ctrllayers['Drainage Lines'] = drainage_layer;
ctrllayers['VIIRS Imagery'] = VIIRSlayer;
let controlsObj = L.control.layers(basemapObj, ctrllayers).addTo(mapObj);

////////////////////////////////////////////////////////////////////////  LISTENERS FOR MAP EVENTS
let startzoom;
const chart_divs = [$("#forecast-chart"), $("#forecast-table"), $("#historical-chart"), $("#historical-table"), $("#seasonal-chart"), $("#flowduration-chart")];
mapObj.on("click", function (event) {
    // delete any existing marker
    if (marker) {mapObj.removeLayer(marker)}
    // get the reachid by querying geoserver
    let meta = drainage_layer.GetFeatureInfo(event);
    reachid = meta[0];
    drain_area = meta[1];
    // put a new marker on the map
    marker = L.marker(event.latlng).addTo(mapObj);
    updateStatusIcons('cleared');
    // clear anything (e.g. old charts) in the chart divs
    for (let i in chart_divs) {chart_divs[i].html('')}
    $("#forecast-table").html('');
    $("#chart_modal").modal('show');
    askAPI();
})
////////////////////////////////////////////////////////////////////////  GET DATA FROM API
function askAPI() {
    if (!reachid) {return}
    updateStatusIcons('load');
    updateDownloadLinks('clear');
    for (let i in chart_divs) {chart_divs[i].html('')}  // clear the contents of old chart divs
    let ftl = $("#forecast_tab_link");  // select divs with jquery so we can reuse them
    let fc = $("#forecast-chart");  // select divs with jquery so we can reuse them
    ftl.tab('show')
    fc.html('<img src="https://www.ashland.edu/sites/all/themes/ashlandecard/2014card/images/load.gif">');
    fc.css('text-align', 'center');
    $.ajax({
        type: 'GET',
        async: true,
        url: '/apps/' + app_url + '/get_streamflow' + L.Util.getParamString({reach_id: reachid, drain_area: drain_area}),
        success: function (html) {
            // forecast tab
            ftl.tab('show');
            fc.html(html['fp']);
            $("#forecast-table").html(html['prob_table']);
            // records tab
            $("#records_tab_link").tab('show');
            $("#records-chart").html(html['rcp']);
            // historical tab
            $("#historical_tab_link").tab('show');
            $("#historical-5-chart").html(html['hp']);
            $("#historical-5-table").html(html['rp_table']);
            // seasonal average tab
            $("#seasonal_avg_tab_link").tab('show');
            $("#seasonal-5-chart").html(html['sp']);
            // flow duration tab
            $("#flow_duration_tab_link").tab('show');
            $("#flowduration-5-chart").html(html['fdp']);
            // update other messages and links
            ftl.tab('show');
            updateStatusIcons('ready');
            updateDownloadLinks('set');
        },
        error: function () {
            updateStatusIcons('fail');
            for (let i in chart_divs) {chart_divs[i].html('')}
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
        $("#download-records-btn").attr('href', '');
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
    let buttons = [$("#download-forecast-btn"), $("#download-records-btn"), $("#download-historical-btn"), $("#download-seasonal-btn")]
    for (let i in buttons) {buttons[i].hide()}
    if (tab === 'forecast') {buttons[0].show();$("#toggle_historical").hide()}
    else if (tab === 'records') {buttons[1].show();$("#toggle_historical").hide()}
    else if (tab === 'historical') {buttons[2].show();$("#toggle_historical").show()}
    else if (tab === 'seasonal') {buttons[3].show();$("#toggle_historical").show()}
    else if (tab === 'flowduration') {$("#toggle_historical").show()}
    fix_chart_sizes(tab);
    $("#resize_charts").attr({'onclick': "fix_chart_sizes('" + tab + "')"})
}
function fix_chart_sizes(tab) {
    let divs = [];
    if (tab === 'forecast') {divs = [$("#forecast-chart .js-plotly-plot")]}
    else if (tab === 'records') {divs = [$("#records-chart .js-plotly-plot")]}
    else if (tab === 'historical') {divs = [$("#historical-5-chart .js-plotly-plot"), $("#historical-int-chart .js-plotly-plot")]}
    else if (tab === 'seasonal') {divs = [$("#seasonal-5-chart .js-plotly-plot"), $("#seasonal-int-chart .js-plotly-plot")];}
    else if (tab === 'flowduration') {divs = [$("#flowduration-5-chart .js-plotly-plot"), $("#flowduration-int-chart .js-plotly-plot")];}
    for (let i in divs) {
        divs[i].css('height', 500);
        Plotly.Plots.resize(divs[i][0]);
    }
}
$("#forecast_tab_link").on('click', function (){fix_buttons('forecast')})
$("#records_tab_link").on('click', function (){fix_buttons('records')})
$("#historical_tab_link").on('click', function (){fix_buttons('historical')})
$("#seasonal_avg_tab_link").on('click', function (){fix_buttons('seasonal')})
$("#flow_duration_tab_link").on('click', function (){fix_buttons('flowduration')})

////////////////////////////////////////////////////////////////////////  UPLOAD OBSERVATIONAL DATA
function uploadCSV() {
    let loading_div = $("#upload_csv_loading");
    let files = $('#upload-csv-input')[0].files;
    let form_data = new FormData();
    Object.keys(files).forEach(function (file) {
        form_data.append('files', files[file]);
    console.log(form_data);
    });
    loading_div.html('<img src="https://www.ashland.edu/sites/all/themes/ashlandecard/2014card/images/load.gif">');
    $.ajax({
        url: '/apps/' + app_url + '/upload_new_observations/',
        type: 'POST',
        data: form_data,
        dataType: 'json',
        processData: false,
        contentType: false,
        success: function (response) {
            loading_div.html('<h3>finished successfully</h3>');
        },
        error: function (response) {
            loading_div.html('<h3>There was an expected problem uploading your csv file</h3>')
        }
    });
}