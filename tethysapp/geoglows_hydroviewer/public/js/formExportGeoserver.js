$('#geoserver-form').submit(function (evt) {
	evt.preventDefault();
	$("#geoserver-upload-loading").show();
	let ajax_args = {
		url: $(this).attr("action"),
		type: $(this).attr("method"),
		data: $(this).serialize(),
		timeout: 0,
	};
	$.ajax(ajax_args).done(function (response) {
		if (response['status'] !== 'success') {
			return
		}
		$.ajax(ajax_args).done(function (response) {
			$("#geoserver-upload-loading").hide()
			if (response['status'] === 'success') {
				alert('Your shapefiles were successfully uploaded to a geoserver. This page will now refresh.');
				window.location.reload(true)
			}
		})
	});
});