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
const basemaps = {
    "ESRI Topographic": L.esri.basemapLayer('Topographic').addTo(mapObj),
    "ESRI Terrain": L.layerGroup([L.esri.basemapLayer('Terrain'), L.esri.basemapLayer('TerrainLabels')]),
    "ESRI Grey": L.esri.basemapLayer('Gray'),
}

////////////////////////////////////////////////////////////////////////  MAP FUNCTIONS AND VARIABLES
showBoundaryLayers();
////////////////////////////////////////////////////////////////////////  LISTENERS FOR MAP LAYERS
let startzoom;
let bc_threshold = 6;
let cd_threshold = 8;
mapObj.on("mousemove", function (event) {
    $("#mouse-position").html('Lat: ' + event.latlng.lat.toFixed(5) + ', Lon: ' + event.latlng.lng.toFixed(5));
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