var cssPagedMedia = (function() {
	var style = document.createElement('style');
	document.head.appendChild(style);
	return function(rule) {
		style.innerHTML = rule;
	};
}());

cssPagedMedia.size = function(size) {
	cssPagedMedia('@page {size: ' + size + '}');
};

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
			} else {
				$id.find('input[name=' + i + ']').prop('checked', false);
				if (i !== 'enabled') {
					$id.find('input[name=' + i + ']').change();
				}
			}
		} else {
			$id.find('input[name=' + i + ']').val(data[i]);
		}
	}
	cssPagedMedia.size($id.find('input[name=page_size]').val());
	$id.find('.preset').removeClass('active');
	$('#' + $id.find('input[name=print_preset]').val()).addClass('active')
	$id.find('button').each(function() {
		$(this).data('item-id', $id);
	});
	$id.find('input').data('item-id', $id);
}

var selectPreset = function(preset) {
	var presets = {
		'list' : {
			'print_preset' : 'list',
			'print_show_cover' : 'TRUE',
			'print_show_album_info' : 'TRUE',
			'print_show_album_controls' : 'TRUE',
			'print_show_tracks' : 'TRUE',
			'print_show_general_controls' : 'FALSE',
			'print_num_cols' : 1,
			'print_tile_size' : ''
		},
		'tiles' : {
			'print_preset' : 'tiles',
			'print_show_cover' : 'TRUE',
			'print_show_album_info' : 'FALSE',
			'print_show_album_controls' : 'FALSE',
			'print_show_tracks' : 'FALSE',
			'print_show_general_controls' : 'TRUE',
			'print_num_cols' : 3,
			'print_tile_size' : ''
		},
		'cd' : {
			'print_preset' : 'cd',
			'print_show_cover' : 'FALSE',
			'print_show_album_info' : 'FALSE',
			'print_show_album_controls' : 'TRUE',
			'print_show_tracks' : 'TRUE',
			'print_show_general_controls' : 'FALSE',
			'print_num_cols' : 1,
			'print_tile_size' : '12'
		}
	};
	var $id = $('#config');
	$id.find('.preset').removeClass('active');
	$('#' + $id.find('input[name=print_preset]').val()).addClass('active');
	fillInElement($id, presets[preset]);
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

	// make the config boxes the same height
	$('.box').matchHeight();

	// Add tooltips
	$('[data-toggle="tooltip"]').tooltip();

	// Add event handlers for everything. Most are delegated at the bubble-up
	// stage.
	$('#config-save').click(function() {
		saveConfig($(this).data('item-id'));
	});
	
	// select presets
	$('#list').click( function() {
		selectPreset('list');
	});
	$('#tiles').click( function() {
		selectPreset('tiles');
	});
	$('#cd').click( function() {
		selectPreset('cd');
	});

	// Change page media size if option is changed
	$('input[name=page_size]').change(function() {
		cssPagedMedia.size($(this).val());
	});
});
