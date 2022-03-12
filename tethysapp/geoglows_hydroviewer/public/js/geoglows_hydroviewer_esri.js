mapObj.createPane("watershedlayers")
mapObj.getPane("watershedlayers").style.zIndex = 250
mapObj.createPane("viirs")
mapObj.getPane("viirs").style.zIndex = 200
// add the legends box to the map
let legend = L.control({position: "bottomright"})
legend.onAdd = function () {
    let div = L.DomUtil.create("div", "legend")
    let start =
        '<div><svg width="20" height="20" viewPort="0 0 20 20" version="1.1" xmlns="http://www.w3.org/2000/svg">'
    div.innerHTML =
        '<div class="legend">' +
        start +
        '<polyline points="19 1, 1 6, 19 14, 1 19" stroke="purple" fill="transparent" stroke-width="2"/></svg> 20-yr Return Period Flow </div>' +
        start +
        '<polyline points="19 1, 1 6, 19 14, 1 19" stroke="red" fill="transparent" stroke-width="2"/></svg> 10-yr Return Period Flow </div>' +
        start +
        '<polyline points="19 1, 1 6, 19 14, 1 19" stroke="gold" fill="transparent" stroke-width="2"/></svg> 2-yr Return Period Flow</div>' +
        start +
        '<polyline points="19 1, 1 6, 19 14, 1 19" stroke="blue" fill="transparent" stroke-width="2"/></svg> Stream Line </div>' +
        "</div>"
    return div
}
legend.addTo(mapObj)
////////////////////////////////////////////////////////////////////////  ESRI LAYER ANIMATION CONTROLS
let layerAnimationTime = new Date()
layerAnimationTime = new Date(layerAnimationTime.toISOString())
layerAnimationTime.setUTCHours(0)
layerAnimationTime.setUTCMinutes(0)
layerAnimationTime.setUTCSeconds(0)
layerAnimationTime.setUTCMilliseconds(0)
const currentDate = $("#current-map-date")
const startDateTime = new Date(layerAnimationTime)
const endDateTime = new Date(layerAnimationTime.setUTCHours(15 * 24))
layerAnimationTime = new Date(startDateTime)
currentDate.html(layerAnimationTime)
const slider = $("#time-slider")
slider.change(() => refreshLayerAnimation())

const refreshLayerAnimation = () => {
    layerAnimationTime = new Date(startDateTime)
    layerAnimationTime.setUTCHours(slider.val() * 3)
    currentDate.html(layerAnimationTime)
    globalLayer.setTimeRange(layerAnimationTime, endDateTime)
}

let animate = false

const playAnimation = (once = false) => {
    if (!animate) {
        return
    }
    if (layerAnimationTime < endDateTime) {
        slider.val(Number(slider.val()) + 1)
    } else {
        slider.val(0)
    }
    refreshLayerAnimation()
    if (once) {
        animate = false
        return
    }
    setTimeout(playAnimation, 750)
}

$("#animationPlay").click(function () {
    animate = true
    playAnimation()
})
$("#animationStop").click(function () {
    animate = false
})
$("#animationPlus1").click(function () {
    animate = true
    playAnimation(true)
})
$("#animationBack1").click(function () {
    if (layerAnimationTime > startDateTime) {
        slider.val(Number(slider.val()) - 1)
    } else {
        slider.val((24 / 3) * 15)
    }
    refreshLayerAnimation()
})
////////////////////////////////////////////////////////////////////////  ADD WMS LAYERS FOR DRAINAGE LINES, VIIRS, ETC - SEE HOME.HTML TEMPLATE
let VIIRSlayer = L.tileLayer(
    "https://floods.ssec.wisc.edu/tiles/RIVER-FLDglobal-composite/{z}/{x}/{y}.png",
    {
        layers: "RIVER-FLDglobal-composite: Latest",
        crossOrigin: true,
        pane: "viirs"
    }
)
const globalLayer = L.esri
    .dynamicMapLayer({
        url: "https://livefeeds2.arcgis.com/arcgis/rest/services/GEOGLOWS/GlobalWaterModel_Medium/MapServer",
        useCors: false,
        layers: [0],
        from: startDateTime,
        to: endDateTime
    })
    .addTo(mapObj)
L.control
    .layers(
        basemapsJson,
        {
            "Stream Network": globalLayer,
            "Gauge Network": gaugeNetwork,
            "VIIRS Imagery": VIIRSlayer
        },
        {collapsed: false}
    )
    .addTo(mapObj)

mapObj.on("click", function (event) {
    if (mapObj.getZoom() <= 9.5) {
        mapObj.flyTo(event.latlng, 10);
        return
    } else {
        mapObj.flyTo(event.latlng)
    }
    if (mapMarker) {
        mapObj.removeLayer(mapMarker)
    }
    mapMarker = L.marker(event.latlng).addTo(mapObj)
    updateStatusIcons("identify")
    $("#chart_modal").modal("show")

    L.esri
        .identifyFeatures({url: "https://livefeeds2.arcgis.com/arcgis/rest/services/GEOGLOWS/GlobalWaterModel_Medium/MapServer"})
        .on(mapObj)
        // query bounding box
        // .at(L.latLngBounds(
        //     [event.latlng['lat'] - .05, event.latlng['lng'] - .05],
        //     [event.latlng['lat'] + .05, event.latlng['lng'] + .05],))

        // querying point with tolerance
        .at([event.latlng["lat"], event.latlng["lng"]])
        .tolerance(10) // map pixels to buffer search point
        .precision(3) // decimals in the returned coordinate pairs
        // .returnGeometry(false)  // include geojson geometry
        .run(function (error, featureCollection) {
            if (error) {
                updateStatusIcons("fail")
                alert("Error finding the reach_id")
                return
            }
            SelectedSegment.clearLayers()
            SelectedSegment.addData(featureCollection.features[0].geometry)
            REACHID = featureCollection.features[0].properties["COMID (Stream Identifier)"]
            clearChartDivs()
            hideGetHistorical()
            hideHistoricalTabs()
            hideBiasCalibrationTabs()
            updateStatusIcons("load")
            updateDownloadLinks("clear")
            setupDatePicker()
        })
})
