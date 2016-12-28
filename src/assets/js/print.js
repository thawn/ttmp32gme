var getElementValues = function($id) {
	var filterVars = {};
	$id.find('input').not(':button').each(function() {
		if ($(this).is(':checkbox')) {
			filterVars[this.name] = testCheckBox(this);
		} else {
			filterVars[this.name] = $(this).val();
		}
	});
	return filterVars;
}

var fillInElement = function($id, data) {
	for ( var i in data) {
		if (data[i] === 'TRUE' || data[i] === 'FALSE') {
			if (data[i] === 'TRUE') {
				$id.find('input[name=' + i + ']').prop('checked', true);
				if (i !== 'enabled') {
					$id.find('input[name=' + i + ']').change();
				}
			}
		} else {
			$id.find('input[name=' + i + ']').val(data[i]);
		}
	}
	$id.find('button').each(function() {
		$(this).data('item-id', $id);
	});
	$id.find('input').data('item-id', $id);
}

var getConfig = function() {
	var filterVars = {};
	$.post(document.baseURI,
			'action=get_config&data=' + escape(JSON.stringify(filterVars)),
			function(data) {
				if (data.success) {
					var $id = $('#config');
					fillInElement($id, data.element);

				} else {
					notify($('#config-save'), '', data.statusText, 'bg-danger', 4000);
				}
			}, 'json').fail(function(data) {
		notify($('#config-save'), '', data.statusText, 'bg-danger', 4000);
	});
}

var saveConfig = function($id) {
	var elementVars = getElementValues($id);
	$.post(
			document.baseURI,
			'action=save_config&data=' + escape(JSON.stringify(elementVars)),
			function(data) {
				if (data.success) {
					fillInElement($id, data.element);
					notify($id.find('button.edit-button'), '', data.statusText, 'bg-success',
							2000);
				} else {
					notify($id.find('button.edit-button'), '', data.statusText, 'bg-danger',
							4000);
				}
			}, 'json').fail(
			function() {
				notify($id.find('button.edit-button'), '', 'Connection error', 'bg-danger',
						4000);
			});
}

$(function() {
	// fetch the configuration from the database
	getConfig();
	// Add tooltips
	$('[data-toggle="tooltip"]').tooltip();

	// Add event handlers for everything. Most are delegated at the bubble-up
	// stage.
	$('#config-save').click( function() {
		saveConfig($(this).data('item-id'));
	});
});
