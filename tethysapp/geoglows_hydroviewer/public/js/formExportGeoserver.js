$('#geoserver-form').submit(function (evt) {
	evt.preventDefault();
	$("#geoserver-upload-loading").show();
	let url = $(this).attr("action");
	let type = $(this).attr("method");
	let data = $(this).serialize();
	$.ajax({
		url: url,
		type: type,
		data: data,
	}).done(function () {
		$.ajax({
			url: url,
			type: type,
			data: data,
		}).done(function (response) {
			$("#geoserver-upload-loading").hide()
			if (response['status'] === 'success') {
				alert('Your shapefiles were successfully uploaded to a geoserver. This page will now refresh.');
				window.location.reload(true)
			}
		})
	});
});