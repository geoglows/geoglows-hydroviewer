$('#shapefile-form').submit(function (evt) {
    evt.preventDefault();
	$.ajax({
		url : $(this).attr("action"),
		type: $(this).attr("method"),
        data: new FormData(this),
        dataType: 'json',
        contentType: false,
        cache: false,
        processData: false,
	}).done(function(response){ //
		console.log(response);
		if (response['status'] === 'success') {
			alert('Your shapefiles were successfully uploaded and processed. This page will now refresh.')
			window.location.reload(true)
		}
	});
});