$('#geoserver-form').submit(function (evt) {
    evt.preventDefault();
    $("#geoserver-upload-loading").show()
	$.ajax({
		url : $(this).attr("action"),
		type: $(this).attr("method"),
		data : $(this).serialize(),
	}).done(function(response){ //
	    $("#geoserver-upload-loading").hide()
		if (response['status'] === 'success') {
			alert('Your shapefiles were successfully uploaded to a geoserver. This page will now refresh.')
			window.location.reload(true)
		}
	});
});