const mapObj = L.map('preview-map', {
    zoom: 3,
    minZoom: 2,
    maxZoom: 12,
    boxZoom: true,
    maxBounds: L.latLngBounds(L.latLng(-100, -225), L.latLng(100, 225)),
    center: [20, 0],
})
const basemapsJson = {
    "ESRI Topographic": L.esri.basemapLayer('Topographic').addTo(mapObj),
    "ESRI Terrain": L.layerGroup([L.esri.basemapLayer('Terrain'), L.esri.basemapLayer('TerrainLabels')]),
    "ESRI Grey": L.esri.basemapLayer('Gray'),
}
const message = L.control({position: 'bottomleft'});
message.onAdd = function () {
    let div = L.DomUtil.create('div', 'well well-sm');
    div.innerHTML = '<p>This map is a preview of your hydroviewer</p>';
    return div;
};
message.addTo(mapObj);

const bounds = L.geoJSON(false);
if (boundaries) {
    $.ajax({
        type: 'GET',
        url: URLgetBoundary,
        data: {'project': project},
        dataType: 'json',
        success: function (response) {
            bounds.addData(response).addTo(mapObj);
            mapObj.fitBounds(bounds.getBounds());
        },
    });
}

let drainagelines;
let catchments;
if (exported) {
    catchments = L.tileLayer.wms(geoserver_wms,
        {"format": "image/png", "transparent": true, "layers": workspace + ":" + catchmentLayer});
    drainagelines = L.tileLayer.wms(geoserver_wms,
        {"format": "image/png", "transparent": true, "layers": workspace + ":" + drainageLayer}).addTo(mapObj);
} else {
    drainagelines = L.geoJSON(false);
    catchments = L.geoJSON(false);
}

const globalLayer = L.esri.dynamicMapLayer({
    url: 'https://livefeeds2.arcgis.com/arcgis/rest/services/GEOGLOWS/GlobalWaterModel_Medium/MapServer',
    useCors: false,
    layers: [0],
});

L.control.layers(
    basemapsJson,
    {
        'Global Stream Network': globalLayer,
        'Project Boundaries': bounds,
        'Project Catchments': catchments,
        'Project Drainage Lines': drainagelines
    },
    {'collapsed': false}
).addTo(mapObj);