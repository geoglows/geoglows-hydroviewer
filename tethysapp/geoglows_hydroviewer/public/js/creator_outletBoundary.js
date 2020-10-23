const mapObj = L.map('map', {
    zoom: 3,
    minZoom: 2,
    boxZoom: true,
    maxBounds: L.latLngBounds(L.latLng(-100, -225), L.latLng(100, 225)),
    center: [20, 0],
});
let REACHID;
let marker = null;
let SelectedSegment = L.geoJSON(false, {weight: 5, color: '#00008b'}).addTo(mapObj);
const basemapsJson = {
    "ESRI Topographic": L.esri.basemapLayer('Topographic').addTo(mapObj),
    "ESRI Terrain": L.layerGroup([L.esri.basemapLayer('Terrain'), L.esri.basemapLayer('TerrainLabels')]),
    "ESRI Grey": L.esri.basemapLayer('Gray'),
}
//////////////////////////////////////////////////////////////////////// ADD LEGEND LAT LON BOX
// lat/lon tracking box on the bottom left of the map
let latlon = L.control({position: 'bottomleft'});
latlon.onAdd = function () {
    let div = L.DomUtil.create('div', 'well well-sm');
    div.innerHTML = '<div id="mouse-position" style="text-align: center"></div>';
    return div;
};
latlon.addTo(mapObj);
mapObj.on("mousemove", function (event) {
    $("#mouse-position").html('Lat: ' + event.latlng.lat.toFixed(4) + ', Lon: ' + event.latlng.lng.toFixed(4));
});
const globalLayer = L.esri.dynamicMapLayer({
    url: 'https://livefeeds2.arcgis.com/arcgis/rest/services/GEOGLOWS/GlobalWaterModel_Medium/MapServer',
    useCors: false,
    layers: [0],
}).addTo(mapObj);
L.control.layers(basemapsJson, {
    'Stream Network': globalLayer,
}, {'collapsed': false}).addTo(mapObj);

mapObj.on("click", function (event) {
    if (mapObj.getZoom() <= 9.5) {
        mapObj.flyTo(event.latlng, 10);
        return
    } else {
        mapObj.flyTo(event.latlng)
    }
    if (marker) {
        mapObj.removeLayer(marker)
    }
    marker = L.marker(event.latlng).addTo(mapObj);
    L.esri.identifyFeatures({
        url: 'https://livefeeds2.arcgis.com/arcgis/rest/services/GEOGLOWS/GlobalWaterModel_Medium/MapServer'
    })
        .on(mapObj)
        // querying point with tolerance
        .at([event.latlng['lat'], event.latlng['lng']])
        .tolerance(10)  // map pixels to buffer search point
        .precision(3)  // decimals in the returned coordinate pairs
        .run(function (error, featureCollection) {
            if (error) {
                alert('Error finding the reach_id');
                return
            }
            SelectedSegment.clearLayers();
            SelectedSegment.addData(featureCollection.features[0].geometry)
            REACHID = featureCollection.features[0].properties["COMID (Stream Identifier)"];

            $.ajax({
                type: 'GET',
                url: URL_findUpstreamBoundaries,
                data: {reachid: REACHID, project: project},
                dataType: 'json',
                success: function (response) {

                },
                error: function (response) {

                },
            })
        })
});
