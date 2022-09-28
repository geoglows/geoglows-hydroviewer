const mapObj = L.map("map", {
    zoom: 3,
    minZoom: 2,
    boxZoom: true,
    maxBounds: L.latLngBounds(L.latLng(-100, -225), L.latLng(100, 225)),
    center: [20, 0]
})
let REACHID
let CURRENTDATE
let mapMarker = null
let controlsObj
let SelectedSegment = L.geoJSON(false, { weight: 5, color: "#00008b" }).addTo(mapObj)

const basemapsJson = {
    "ESRI Topographic": L.esri.basemapLayer("Topographic").addTo(mapObj),
    "ESRI Terrain": L.layerGroup([
        L.esri.basemapLayer("Terrain"),
        L.esri.basemapLayer("TerrainLabels")
    ]),
    "ESRI Grey": L.esri.basemapLayer("Gray")
}

let gaugeNetwork = L.geoJSON(false, {
    onEachFeature: function(feature, layer) {
        REACHID = feature.properties.GEOGLOWSID
        layer.on("click", function(event) {
            L.DomEvent.stopPropagation(event)
            getBiasCorrectedPlots(feature.properties)
        })
    },
    pointToLayer: function(feature, latlng) {
        return L.circleMarker(latlng, {
            radius: 6,
            fillColor: "#ff0000",
            color: "#000000",
            weight: 1,
            opacity: 1,
            fillOpacity: 1
        })
    }
})
//////////////////////////////////////////////////////////////////////// ADD LEGEND LAT LON BOX
// lat/lon tracking box on the bottom left of the map
let latlon = L.control({ position: "bottomleft" })
latlon.onAdd = function() {
    let div = L.DomUtil.create("div", "well well-sm")
    div.innerHTML = '<div id="mouse-position" style="text-align: center"></div>'
    return div
}
latlon.addTo(mapObj)
mapObj.on("mousemove", function(event) {
    $("#mouse-position").html(
        "Lat: " + event.latlng.lat.toFixed(4) + ", Lon: " + event.latlng.lng.toFixed(4)
    )
})
//////////////////////////////////////////////////////////////////////// OTHER UTILITIES ON THE LEFT COLUMN
function findReachID() {
    $.ajax({
        type: "GET",
        async: true,
        url:
            URL_find_reach_id +
            L.Util.getParamString({
                reach_id: prompt("Please enter a Reach ID to search for")
            }),
        success: function(response) {
            if (mapMarker) {
                mapObj.removeLayer(mapMarker)
            }
            mapMarker = L.marker(L.latLng(response["lat"], response["lon"])).addTo(mapObj)
            mapObj.flyTo(L.latLng(response["lat"], response["lon"]), 9)
        },
        error: function() {
            alert("Unable to find the reach_id specified")
        }
    })
}
function findLatLon() {
    if (mapMarker) {
        mapObj.removeLayer(mapMarker)
    }
    let ll = prompt(
        "Enter a latitude and longitude coordinate pair separated by a comma. For example, to get to BYU you would enter: 40.25, -111.65",
        "40.25, -111.65"
    )
    ll = ll
        .replace(" ", "")
        .replace("(", "")
        .replace(")", "")
        .split(",")
    mapMarker = L.marker(L.latLng(ll[0], ll[1])).addTo(mapObj)
    mapObj.flyTo(L.latLng(ll[0], ll[1]), 9)
}
////////////////////////////////////////////////////////////////////////  GAUGE NETWORKS STUFF
function getGaugeGeoJSON() {
    gaugeNetwork.clearLayers()
    let network = $("#gauge_networks").val()
    if (network === "") {
        return
    }
    $.ajax({
        type: "GET",
        async: true,
        url: URL_get_gauge_geojson + L.Util.getParamString({ network: network }),
        success: function(geojson) {
            gaugeNetwork.addData(geojson).addTo(mapObj)
            mapObj.flyToBounds(gaugeNetwork.getBounds())
        },
        error: function() {
            alert("Error retrieving the locations of the gauge network")
        }
    })
}

$("#gauge_networks").change(function() {
    getGaugeGeoJSON()
})
//////////////////////////////////////////////////////////////////////// UPDATE DOWNLOAD LINKS FUNCTION
function updateDownloadLinks(type) {
    if (type === "clear") {
        $("#download-forecast-btn").attr("href", "")
        $("#download-historical-btn").attr("href", "")
    } else if (type === "set") {
        $("#download-forecast-btn").attr(
            "href",
            endpoint +
                "ForecastStats/?reach_id=" +
                REACHID +
                "&forecast_date=" +
                getFormattedDate(CURRENTDATE)
        )
        $("#download-historical-btn").attr(
            "href",
            endpoint + "HistoricSimulation/?reach_id=" + REACHID
        )
    }
}
////////////////////////////////////////////////////////////////////////  UPLOAD OBSERVATIONAL DATA
$("#hydrograph-csv-form").on("submit", function(e) {
    e.preventDefault()
    let upload_stats = $("#hydrograph-csv-status")
    upload_stats.html("in progress...")
    $.ajax({
        type: "POST",
        url: URL_upload_new_observations,
        data: new FormData(this),
        dataType: "json",
        contentType: false,
        cache: false,
        processData: false,
        success: function(response) {
            upload_stats.html("uploaded finished successfully.")
            let uploaded_input = $("#uploaded_observations")
            uploaded_input.empty()
            let new_file_list = response["new_file_list"]
            for (let i = 0; i < new_file_list.length; i++) {
                uploaded_input.append(
                    '<option value="' +
                        new_file_list[i][1] +
                        '">' +
                        new_file_list[i][0] +
                        "</option>"
                )
            }
        },
        error: function(response) {
            upload_stats.html("failed to upload. " + response["error"])
        }
    })
})

////////////////////////////////////////////////////////////////////////  GET DATA FROM API AND MANAGING PLOTS
const chart_divs = [
    $("#forecast-chart"),
    $("#forecast-table"),
    $("#historical-chart"),
    $("#historical-table"),
    $("#daily-avg-chart"),
    $("#monthly-avg-chart"),
    $("#flowduration-chart"),
    $("#volume_plot"),
    $("#scatters"),
    $("#stats_table")
]

function setupDatePicker() {
    let date = new Date()
    // let today = new Date(date.getFullYear(), date.getMonth(), date.getDate())

    $.ajax({
        type: "GET",
        async: true,
        data: { reach_id: REACHID },
        url: URL_getAvailableDates,
        success: function(response) {
            let dates = response["dates"]
            let latestAvailableDate = dates.sort(
                (a, b) => parseFloat(b) - parseFloat(a)
            )[0]
            let selectedDate = new Date(
                latestAvailableDate.slice(0, 4),
                parseInt(latestAvailableDate.slice(4, 6)) - 1,
                latestAvailableDate.slice(6, 8)
            )
            CURRENTDATE = selectedDate
            $("#forecast_date")
                .datepicker({
                    format: "mm/dd/yyyy",
                    startDate: "-45d",
                    endDate: selectedDate,
                    autoclose: true,
                    beforeShowDay: function(date) {
                        let dateString =
                            date.getFullYear() +
                            ("0" + (date.getMonth() + 1)).slice(-2) +
                            ("0" + date.getDate()).slice(-2)

                        return {
                            enabled: dates.indexOf(dateString) >= 0
                        }
                    }
                })
                .on("changeDate", function(e) {
                    if (e.date.getTime() !== CURRENTDATE.getTime()) {
                        CURRENTDATE = e.date
                        chart_divs[0].html("")
                        chart_divs[1].html("")
                        hideGetHistorical()
                        hideHistoricalTabs()
                        hideBiasCalibrationTabs()
                        updateStatusIcons("load")
                        updateDownloadLinks("clear")
                        getForecastData()
                    }
                })
            $("#forecast_date").datepicker("update", selectedDate)
            getForecastData()
        },
        error: function() {
            updateStatusIcons("fail")
            REACHID = null
        }
    })
}
function getFormattedDate(dateObj) {
    return `${dateObj.getFullYear()}${("0" + (dateObj.getMonth() + 1)).slice(-2)}${(
        "0" + dateObj.getDate()
    ).slice(-2)}.00`
}
function getForecastData() {
    let ftl = $("#forecast_tab_link") // select divs with jquery so we can reuse them
    ftl.tab("show")
    let fc = chart_divs[0]
    fc.html(
        '<img src="https://www.ashland.edu/sites/all/themes/ashlandecard/2014card/images/load.gif">'
    )
    fc.css("text-align", "center")
    let dateOffset = 24 * 60 * 60 * 1000 * 7 // 7 days converted to milliseconds, the js time unit
    let start_date = new Date()
    start_date.setTime(CURRENTDATE.getTime() - dateOffset)
    $.ajax({
        type: "GET",
        async: true,
        data: {
            reach_id: REACHID,
            end_date: getFormattedDate(CURRENTDATE),
            start_date: getFormattedDate(start_date)
        },
        url: URL_getForecastData,
        success: function(response) {
            // forecast tab
            ftl.tab("show")
            fc.html(response["plot"])
            $("#forecast-table").html(response["table"])
            updateDownloadLinks("set")
            updateStatusIcons("ready")
            showGetHistorical()
            showBiasCalibrationTabs()
        },
        error: function() {
            updateStatusIcons("fail")
            REACHID = null
        }
    })
}

function getHistoricalData() {
    updateStatusIcons("load")
    updateDownloadLinks("clear")
    let tl = $("#historical_tab_link") // select divs with jquery so we can reuse them
    tl.tab("show")
    let plotdiv = chart_divs[2]
    plotdiv.html(
        '<img src="https://www.ashland.edu/sites/all/themes/ashlandecard/2014card/images/load.gif">'
    )
    plotdiv.css("text-align", "center")
    $.ajax({
        type: "GET",
        async: true,
        data: { reach_id: REACHID },
        url: URL_getHistoricalData,
        success: function(response) {
            showHistoricalTabs()
            // historical tab
            tl.tab("show")
            $("#get-historical-btn").hide()
            plotdiv.html(response["plot"])
            $("#historical-table").html(response["table"])
            // average flows tab
            $("#avg_flow_tab_link").tab("show")
            $("#daily-avg-chart").html(response["dayavg"])
            $("#monthly-avg-chart").html(response["monavg"])
            // flow duration tab
            $("#flow_duration_tab_link").tab("show")
            $("#flowduration-chart").html(response["fdp"])
            // update other messages and links
            tl.tab("show")
            updateStatusIcons("ready")
            updateDownloadLinks("set")
        },
        error: function() {
            updateStatusIcons("fail")
        }
    })
}

function getBiasCorrectedPlots(gauge_metadata) {
    let data
    if (gauge_metadata !== false) {
        data = gauge_metadata
        data["gauge_network"] = $("#gauge_networks").val()
    } else if (!REACHID) {
        alert(
            "No Reach-ID has been chosen. You must successfully retrieve streamflow before attempting calibration"
        )
        return
    } else {
        let csv = $("#uploaded_observations").val()
        data = {
            reach_id: REACHID,
            observation: csv
        }
        if (
            !confirm(
                'You are about to perform bias correction on reach_id "' +
                    String(REACHID) +
                    '" with uploaded ' +
                    'observed steamflow file "' +
                    csv +
                    '". Are you sure you want to continue?'
            )
        ) {
            return
        }
    }
    updateStatusIcons("load")
    updateDownloadLinks("clear")
    $("#chart_modal").modal("show")
    $("#bias_correction_tab_link").show()
    $.ajax({
        type: "GET",
        async: true,
        data: data,
        url: URL_getBiasAdjusted,
        success: function(html) {
            // forecast tab
            $("#forecast_tab_link").tab("show")
            $("#forecast-chart").append(html["correct_hydro"])
            // historical tab
            $("#historical_tab_link").tab("show")
            $("#historical-chart").html(html["new_hist"])
            $("#historical-table").html("")
            // average flows tab
            $("#avg_flow_tab_link").tab("show")
            $("#daily-avg-chart").html(html["day_avg"])
            $("#monthly-avg-chart").html(html["month_avg"])
            // flow duration curve
            $("#flow_duration_tab_link").tab("show")
            $("#flowduration-chart").html(html["flowdur_plot"])
            // stats tab
            $("#bias_correction_tab_link").tab("show")
            $("#stats_table").html(html["stats_table"])
            $("#volume_plot").html(html["volume_plot"])
            $("#scatters").html(html["scatters"])
            $("#bias_correction_tab_link").tab("show")
            updateStatusIcons("ready")
            updateDownloadLinks("set")
        },
        error: function() {
            updateStatusIcons("fail")
        }
    })
}

//////////////////////////////////////////////////////////////////////// UPDATE STATUS ICONS FUNCTION
function updateStatusIcons(type) {
    let statusObj = $("#request-status")
    if (type === "identify") {
        statusObj.html(" (Getting Stream ID)")
        statusObj.css("color", "orange")
    } else if (type === "load") {
        statusObj.html(" (Loading ID " + REACHID + ")")
        statusObj.css("color", "orange")
    } else if (type === "ready") {
        statusObj.html(" (Ready)")
        statusObj.css("color", "green")
    } else if (type === "fail") {
        statusObj.html(" (Failed)")
        statusObj.css("color", "red")
    } else if (type === "cleared") {
        statusObj.html(" (Cleared)")
        statusObj.css("color", "grey")
    }
}

function fix_buttons(tab) {
    let buttons = [
        $("#download-forecast-btn"),
        $("#download-historical-btn"),
        $("#start-bias-correction-btn")
    ]
    for (let i in buttons) {
        buttons[i].hide()
    }
    if (tab === "forecast") {
        buttons[0].show()
    } else if (tab === "historical") {
        buttons[1].show()
    } else if (tab === "biascorrection") {
        buttons[2].show()
    }
    fix_chart_sizes(tab)
    $("#resize_charts").attr({ onclick: "fix_chart_sizes('" + tab + "')" })
}
function fix_chart_sizes(tab) {
    let divs = []
    if (tab === "forecast") {
        divs = [$("#forecast-chart .js-plotly-plot")]
    } else if (tab === "historical") {
        divs = [$("#historical-5-chart .js-plotly-plot")]
    } else if (tab === "averages") {
        divs = [
            $("#daily-avg-chart .js-plotly-plot"),
            $("#monthly-avg-chart .js-plotly-plot")
        ]
    } else if (tab === "flowduration") {
        divs = [$("#flowduration-5-chart .js-plotly-plot")]
    } else if (tab === "biascorrection") {
        divs = [$("#volume_plot .js-plotly-plot"), $("#scatters .js-plotly-plot")]
    }
    for (let i in divs) {
        try {
            divs[i].css("height", 500)
            Plotly.Plots.resize(divs[i][0])
        } catch (e) {}
    }
}

function clearChartDivs() {
    for (let i in chart_divs) {
        chart_divs[i].html("")
    }
}

function showGetHistorical() {
    $("#historical_tab_link").show()
    $("#get-historical-btn").show()
}

function hideGetHistorical() {
    $("#historical_tab_link").hide()
    $("#get-historical-btn").hide()
}

function hideHistoricalTabs() {
    $("#avg_flow_tab_link").hide()
    $("#flow_duration_tab_link").hide()
}

function showHistoricalTabs() {
    $("#avg_flow_tab_link").show()
    $("#flow_duration_tab_link").show()
}

function hideBiasCalibrationTabs() {
    $("#bias_correction_tab_link").hide()
}

function showBiasCalibrationTabs() {
    $("#bias_correction_tab_link").show()
}

$("#forecast_tab_link").on("click", function() {
    fix_buttons("forecast")
})
$("#historical_tab_link").on("click", function() {
    fix_buttons("historical")
})
$("#avg_flow_tab_link").on("click", function() {
    fix_buttons("averages")
})
$("#flow_duration_tab_link").on("click", function() {
    fix_buttons("flowduration")
})
$("#bias_correction_tab_link").on("click", function() {
    fix_buttons("biascorrection")
})
