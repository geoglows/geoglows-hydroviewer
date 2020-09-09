function processShapefiles() {
    let load_bar = $("#loading-bar-div");
    let progress_list = $("#process-callback-list");
    if (shapefiles) {
        if (!confirm('Shapefiles have already been created for this project, would you like to delete them then, ' +
            'recreate them for the current project boundaries?')) {
            return
        }
    }
    load_bar.show();
    progress_list.html('');
    progress_list.append('<li>Finding source shapefiles to clip</li>');
    let data = {'project': project};
    $.ajax({
        type: 'GET',
        url: URLidRegion,
        data: data,
        dataType: 'json',
        success: function (response1) {
            progress_list.append('<li>Found region: ' + response1['region'] + '</li>');
            progress_list.append('<li>Clipping Drainagelines</li>');
            data['region'] = response1['region']
            data['shapefile'] = 'drainageline'
            $.ajax({
                type: 'GET',
                url: URLclip,
                data: data,
                dataType: 'json',
                success: function () {
                    data['shapefile'] = 'catchment'
                    progress_list.append('<li>Clipped</li>');
                    progress_list.append('<li>Clipping Catchments</li>');
                    $.ajax({
                        type: 'GET',
                        url: URLclip,
                        data: data,
                        dataType: 'json',
                        success: function () {
                            progress_list.append('<li>Clipped</li>');
                            progress_list.append('<li>DONE!</li>');
                            load_bar.hide();
                            alert('Your shapefiles were created successfully. This page will now refresh.')
                            window.location.reload(true)
                        },
                        error: function () {
                            progress_list.append('<li>FAILED</li>');
                            load_bar.hide();
                        },
                    });
                },
                error: function () {
                    progress_list.append('<li>FAILED</li>');
                    load_bar.hide();
                },
            });
        },
        error: function () {
            progress_list.append('<li>FAILED</li>');
            load_bar.hide();
        },
    });
}