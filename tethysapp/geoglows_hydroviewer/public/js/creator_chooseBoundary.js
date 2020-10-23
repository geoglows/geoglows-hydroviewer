let chooseBoundary = ['Afghanistan', 'Albania', 'Algeria', 'American Samoa', 'Andorra', 'Angola', 'Anguilla', 'Antarctica',
    'Antigua and Barbuda', 'Argentina', 'Armenia', 'Aruba', 'Australia', 'Austria', 'Azerbaijan', 'Bahamas',
    'Bahrain', 'Baker Island', 'Bangladesh', 'Barbados', 'Belarus', 'Belgium', 'Belize', 'Benin', 'Bermuda',
    'Bhutan', 'Bolivia', 'Bonaire', 'Bosnia and Herzegovina', 'Botswana', 'Bouvet Island', 'Brazil',
    'British Indian Ocean Territory', 'British Virgin Islands', 'Brunei Darussalam', 'Bulgaria', 'Burkina Faso',
    'Burundi', 'Cambodia', 'Cameroon', 'Canada', 'Cape Verde', 'Cayman Islands', 'Central African Republic', 'Chad',
    'Chile', 'China', 'Christmas Island', 'Cocos Islands', 'Colombia', 'Comoros', 'Congo', 'Congo DRC',
    'Cook Islands', 'Costa Rica', "Côte d'Ivoire", 'Croatia', 'Cuba', 'Curacao', 'Cyprus', 'Czech Republic',
    'Denmark', 'Djibouti', 'Dominica', 'Dominican Republic', 'Ecuador', 'Egypt', 'El Salvador', 'Equatorial Guinea',
    'Eritrea', 'Estonia', 'Ethiopia', 'Falkland Islands', 'Faroe Islands', 'Fiji', 'Finland', 'France',
    'French Guiana', 'French Polynesia', 'French Southern Territories', 'Gabon', 'Gambia', 'Georgia', 'Germany',
    'Ghana', 'Gibraltar', 'Glorioso Island', 'Greece', 'Greenland', 'Grenada', 'Guadeloupe', 'Guam', 'Guatemala',
    'Guernsey', 'Guinea', 'Guinea-Bissau', 'Guyana', 'Haiti', 'Heard Island and McDonald Islands', 'Honduras',
    'Howland Island', 'Hungary', 'Iceland', 'India', 'Indonesia', 'Iran', 'Iraq', 'Ireland', 'Isle of Man',
    'Israel', 'Italy', 'Jamaica', 'Jan Mayen', 'Japan', 'Jarvis Island', 'Jersey', 'Johnston Atoll', 'Jordan',
    'Juan De Nova Island', 'Kazakhstan', 'Kenya', 'Kiribati', 'Kuwait', 'Kyrgyzstan', 'Laos', 'Latvia', 'Lebanon',
    'Lesotho', 'Liberia', 'Libya', 'Liechtenstein', 'Lithuania', 'Luxembourg', 'Madagascar', 'Malawi', 'Malaysia',
    'Maldives', 'Mali', 'Malta', 'Marshall Islands', 'Martinique', 'Mauritania', 'Mauritius', 'Mayotte', 'Mexico',
    'Micronesia', 'Midway Islands', 'Moldova', 'Monaco', 'Mongolia', 'Montenegro', 'Montserrat', 'Morocco',
    'Mozambique', 'Myanmar', 'Namibia', 'Nauru', 'Nepal', 'Netherlands', 'New Caledonia', 'New Zealand',
    'Nicaragua', 'Niger', 'Nigeria', 'Niue', 'Norfolk Island', 'North Korea', 'Northern Mariana Islands', 'Norway',
    'Oman', 'Pakistan', 'Palau', 'Palestinian Territory', 'Panama', 'Papua New Guinea', 'Paraguay', 'Peru',
    'Philippines', 'Pitcairn', 'Poland', 'Portugal', 'Puerto Rico', 'Qatar', 'Réunion', 'Romania',
    'Russian Federation', 'Rwanda', 'Saba', 'Saint Barthelemy', 'Saint Eustatius', 'Saint Helena',
    'Saint Kitts and Nevis', 'Saint Lucia', 'Saint Martin', 'Saint Pierre and Miquelon',
    'Saint Vincent and the Grenadines', 'Samoa', 'San Marino', 'Sao Tome and Principe', 'Saudi Arabia', 'Senegal',
    'Serbia', 'Seychelles', 'Sierra Leone', 'Singapore', 'Sint Maarten', 'Slovakia', 'Slovenia', 'Solomon Islands',
    'Somalia', 'South Africa', 'South Georgia', 'South Korea', 'South Sudan', 'Spain', 'Sri Lanka', 'Sudan',
    'Suriname', 'Svalbard', 'Swaziland', 'Sweden', 'Switzerland', 'Syria', 'Tajikistan', 'Tanzania', 'Thailand',
    'The Former Yugoslav Republic of Macedonia', 'Timor-Leste', 'Togo', 'Tokelau', 'Tonga', 'Trinidad and Tobago',
    'Tunisia', 'Turkey', 'Turkmenistan', 'Turks and Caicos Islands', 'Tuvalu', 'Uganda', 'Ukraine',
    'United Arab Emirates', 'United Kingdom', 'United States', 'Uruguay', 'US Virgin Islands', 'Uzbekistan',
    'Vanuatu', 'Vatican City', 'Venezuela', 'Vietnam', 'Wake Island', 'Wallis and Futuna', 'Yemen', 'Zambia',
    'Zimbabwe'];
$(function () {
    $("#countries").autocomplete({source: chooseBoundary});
});

const mapObj = L.map('map', {
    zoom: 3,
    minZoom: 2,
    boxZoom: true,
    maxBounds: L.latLngBounds(L.latLng(-100, -225), L.latLng(100, 225)),
    center: [20, 0],
})
const basemaps = {"ESRI Topographic": L.esri.basemapLayer('Topographic').addTo(mapObj)}
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
function changeregions(firedfrom) {
    let countryJQ = $("#countries");
    let regionJQ = $("#regions");
    if (firedfrom === 'country') {
        let country = countryJQ.val();
        if (!chooseBoundary.includes(country)) {
            alert('The country "' + country + '" was not found in the list of countries available. Please check spelling and capitalization, and use the input suggestions.');
            return
        }
        regionJQ.val('none');
    } else {
        countryJQ.val('')
    }
    // change to none/empty input
    mapObj.removeLayer(layerRegion);
    if (firedfrom === 'region') {
        layerRegion = regionsESRI();
    } else {
        layerRegion = countriesESRI();
    }
}
$("#regions").change(function () {changeregions('region')});
$("#countriesGO").click(function () {changeregions('country')});
function regionsESRI() {
    let region = $("#regions").val();

    let where = '1=1';
    if (region !== '') {
        where = "REGION = '" + region + "'"
    }
    let params = {
        url: 'https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/World_Regions/FeatureServer/0',
        style: {color: 'rgb(0,0,0)', opacity: 1, weight: 1, fillColor: 'rgba(0,0,0,0)', fillOpacity: 'rgba(0,0,0,0)'},
        outSR: 4326,
        where: where,
        onEachFeature: function (feature, layer) {
            let place = feature.properties.REGION;
            layer.bindPopup('<a class="btn btn-default" role="button">' + place + '</a>');
        },
    };
    if (region !== '') {params['where'] = "REGION = '" + region + "'"}
    let layer = L.esri.featureLayer(params);
    layer.addTo(mapObj);
    layer.query().where(where).bounds(function(error, latLngBounds, response){
        mapObj.flyToBounds(latLngBounds)
    });
    return layer;
}
function countriesESRI() {
    let region = $("#countries").val();
    let where = "NAME='" + region + "'";
    let params = {
        url: 'https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/World__Countries_Generalized_analysis_trim/FeatureServer/0',
        style: {color: 'rgba(0,0,0,1)', opacity: 1, weight: 1, fillColor: 'rgba(0,0,0,0)', fillOpacity: 'rgba(0,0,0,0)'},
        outSR: 4326,
        where: where,
        onEachFeature: function (feature, layer) {
            layer.bindPopup('<a class="btn btn-default" role="button" onclick="getShapeChart(' + "'esri-" + region + "'" + ')">Get timeseries for ' + region + '</a>');
        },
    };
    let layer = L.esri.featureLayer(params);
    layer.addTo(mapObj);
    layer.query().where(where).bounds(function(error, latLngBounds, response){
        mapObj.flyToBounds(latLngBounds)
    });
    return layer;
}
let layerRegion = regionsESRI();
$("#submit-boundaries").click(function () {
    let esri = $("#regions").val();
    console.log(esri);
    if (esri === '' || esri === null) {
        esri = $("#countries").val()
        console.log(esri);
    }
    let data = {
        project: project,
        esri: esri
    }
    let return_home_button = $("#return_to_overview");
    let load_bar = $("#loading-bar-div");
    let load_status = $("#loading-message-div");
    load_bar.show();
    load_status.html('loading...')
    $.ajax({
        type: 'POST',
        url: URL_saveboundaries,
        data: data,
        dataType: 'json',
        success: function () {
            load_bar.hide();
            load_status.html('Uploaded boundary selection successfully. You may now return to the project overview menu')
            return_home_button.show()
        },
        error: function () {
            load_bar.hide();
            load_status.html('Failed to upload for an unknown reason')
            return_home_button.hide()
        },
    });
})