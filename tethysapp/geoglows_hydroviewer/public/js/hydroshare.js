const watersheds_hydroshare_ids = {
    'islands-geoglows': 'e3910292be5e4fd79597c6c91cb084cf',
    'australia-geoglows': '9572eb7fa8744807962b9268593bd4ad',
    'japan-geoglows': 'df5f3e52c51b419d8ee143b919a449b3',
    'east_asia-geoglows': '85ac5bf29cff4aa48a08b8aaeb8e3023',
    'south_asia-geoglows': 'e8f2896be57643eb91220351b961b494',
    'central_asia-geoglows': '383bc50a88ae4711a8d834a322ced2d5',
    'west_asia-geoglows': 'b62087b814804242a1005368d0ba1b82',
    'middle_east-geoglows': '6de72e805b34488ab1742dae64202a29',
    'europe-geoglows': 'c14e1644a94744d8b3204a5be91acaed',
    'africa-geoglows': '121bbce392a841178476001843e7510b',
    'south_america-geoglows': '94f7e730ea034706ae3497a75c764239',
    'central_america-geoglows': '36fae4f0e04d40ccb08a8dd1df88365e',
    'north_america-geoglows': '43ae93136e10439fbf2530e02156caf0'
}
const watersheds = [["Islands", "islands-geoglows"], ["Australia", "australia-geoglows"], ["Japan", "japan-geoglows"], ["East Asia", "east_asia-geoglows"], ["South Asia", "south_asia-geoglows"], ["Central Asia", "central_asia-geoglows"], ["West Asia", "west_asia-geoglows"], ["Middle East", "middle_east-geoglows"], ["Europe", "europe-geoglows"], ["Africa", "africa-geoglows"], ["South America", "south_america-geoglows"], ["Central America", "central_america-geoglows"], ["North America", "north_america-geoglows"]]
////////////////////////////////////////////////////////////////////////  SETUP THE MAP
const mapObj = L.map('map', {
    zoom: 3,
    minZoom: 2,
    maxZoom: 3,
    boxZoom: true,
    maxBounds: L.latLngBounds(L.latLng(-100, -225), L.latLng(100, 225)),
    center: [20, 0],
})
const basemaps = {
    "ESRI Topographic": L.esri.basemapLayer('Topographic').addTo(mapObj),
    "ESRI Terrain": L.layerGroup([L.esri.basemapLayer('Terrain'), L.esri.basemapLayer('TerrainLabels')]),
    "ESRI Grey": L.esri.basemapLayer('Gray'),
}
let controlsObj;
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
let latlon = L.control({position: 'bottomleft'});
latlon.onAdd = function () {
    let div = L.DomUtil.create('div', 'well well-sm');
    div.innerHTML = '<div id="mouse-position" style="text-align: center"></div>';
    return div;
};
legend.addTo(mapObj);
latlon.addTo(mapObj);

////////////////////////////////////////////////////////////////////////  MAP FUNCTIONS AND VARIABLES
function showBoundaryLayers() {
    mapObj.setMaxZoom(3);
    ctrllayers = {};
    for (let i = 0; i < watersheds.length; i++) {
        ctrllayers[watersheds[i][0] + ' Boundary'] = getWatershedComponent(watersheds[i][1] + '-boundary').addTo(mapObj);
    }
    controlsObj = L.control.layers(basemaps, ctrllayers).addTo(mapObj);
}
function getWatershedComponent(layername) {
    let region = layername.replace('-boundary','').replace('-catchment','');
    return L.tileLayer.wms('https://geoserver.hydroshare.org/geoserver/wms', {
        version: '1.1.0',
        layers: 'HS-' + watersheds_hydroshare_ids[region] + ':' + layername + ' ' + layername,
        useCache: true,
        crossOrigin: false,
        format: 'image/png',
        transparent: true,
        opacity: .5,
    })
}

function getDrainageLine(layername) {
    let region = layername.replace('-drainageline','');
    return L.tileLayer.wms('https://geoserver.hydroshare.org/geoserver/wms', {
        version: '1.1.0',
        layers: 'HS-' + watersheds_hydroshare_ids[region] + ':' + layername + ' ' + layername,
        useCache: true,
        crossOrigin: false,
        format: 'image/png',
        transparent: true,
        opacity: 1,
    })
}
// ADD PART AFTER THIS IN THE FUNCTION PAGE
let listlayers = [];
let ctrllayers = {};
let boundary_layer;
let catchment_layer;
let drainage_layer;
showBoundaryLayers();
////////////////////////////////////////////////////////////////////////  LISTENERS FOR MAP LAYERS
let startzoom;
let bc_threshold = 6;
let cd_threshold = 8;
mapObj.on("mousemove", function (event) {
    $("#mouse-position").html('Lat: ' + event.latlng.lat.toFixed(5) + ', Lon: ' + event.latlng.lng.toFixed(5));
});
mapObj.on("click", function (event) {
    if (mapObj.getZoom() <= 8.5) {
        mapObj.flyTo(event.latlng, 9);
        return
    } else {
        mapObj.flyTo(event.latlng)
    }
    if (marker) {
        mapObj.removeLayer(marker)
    }
    marker = L.marker(event.latlng).addTo(mapObj);
    for (let i in chart_divs) {
        chart_divs[i].html('')
    }
    updateStatusIcons('identify');
    $("#chart_modal").modal('show');
    L.esri.identifyFeatures({
        url: 'https://livefeeds2.arcgis.com/arcgis/rest/services/GEOGLOWS/GlobalWaterModel_Medium/MapServer'
    })
        .on(mapObj).tolerance(30)
        .at([event.latlng['lat'], event.latlng['lng']])
        .run(function (error, featureCollection) {
            if (error) {
                updateStatusIcons('fail');
                alert('Error finding the reach_id');
                return
            }
            REACHID = featureCollection.features[0].properties["COMID (Stream Identifier)"];
            updateStatusIcons('load');
            getStreamflowPlots();
        })
});
mapObj.on('zoomstart', function (event) {
    startzoom = event.target.getZoom();
});
mapObj.on('zoomend', function (event) {
    // if you start+end over/under the max/min threshold then there is no need to change layers
    let endzoom = event.target.getZoom();
    if (startzoom >= cd_threshold && endzoom >= cd_threshold) {return}
    if (cd_threshold >= startzoom >= bc_threshold && cd_threshold >= endzoom >= bc_threshold) {return}
    if (startzoom < bc_threshold && endzoom < bc_threshold) {return}

    if (endzoom >= cd_threshold) {
        $("#map").css('cursor', 'pointer');
        mapObj.removeLayer(boundary_layer);
        mapObj.removeLayer(catchment_layer);
        drainage_layer.addTo(mapObj);
        listlayers.push(drainage_layer)
    } else if (endzoom >= bc_threshold) {
        $("#map").css('cursor', '');
        mapObj.removeLayer(boundary_layer);
        catchment_layer.addTo(mapObj);
        mapObj.removeLayer(drainage_layer);
    } else {
        $("#map").css('cursor', '');
        boundary_layer.addTo(mapObj);
        mapObj.removeLayer(catchment_layer);
        mapObj.removeLayer(drainage_layer);
    }
});
$("#watersheds_select_input").change(function () {
    let waterselect = $(this).val();
    for (let i in ctrllayers) {
        controlsObj.removeLayer(ctrllayers[i]);
        mapObj.removeLayer(ctrllayers[i]);
    }
    mapObj.removeControl(controlsObj);
    if (waterselect === '') {
        showBoundaryLayers();
        return
    }
    boundary_layer = getWatershedComponent(waterselect + '-boundary').addTo(mapObj);
    catchment_layer = getWatershedComponent(waterselect + '-catchment');
    drainage_layer = getDrainageLine(waterselect + '-drainageline');
    ctrllayers = {
        'Watershed Boundary': boundary_layer,
        'Catchment Boundaries': catchment_layer,
        'Drainage Lines': drainage_layer,
    };
    controlsObj = L.control.layers(basemaps, ctrllayers).addTo(mapObj);
    mapObj.setMaxZoom(12);
});