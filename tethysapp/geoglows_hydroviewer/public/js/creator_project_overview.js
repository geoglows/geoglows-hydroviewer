const mapObj = L.map('preview-map', {
    zoom: 3,
    minZoom: 2,
    maxZoom: 10,
    boxZoom: true,
    maxBounds: L.latLngBounds(L.latLng(-100, -225), L.latLng(100, 225)),
    center: [20, 0],
})
const basemapObj = {'ESRI Topographic Map': L.esri.basemapLayer('Topographic').addTo(mapObj)}
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
        {"format": "image/png", "transparent": true, "layers": workspace + ":" + drainagelinesLayer}).addTo(mapObj);
} else {
    drainagelines = L.geoJSON(false);
    catchments = L.geoJSON(false);
}

L.control.layers(
    basemapObj,
    {'Project Boundaries': bounds, 'Catchments': catchments, 'Drainage Lines': drainagelines},
    {'collapsed': false}
).addTo(mapObj);