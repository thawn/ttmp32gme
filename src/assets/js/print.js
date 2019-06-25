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

var notify = function($caller, title, message, popover_class, timeout) {
	$caller.attr({
		'title' : title,
		'data-content' : message
	});
	$caller.popover('show');
	$caller.next('.popover').find('.popover-content').addClass(popover_class);
	setTimeout(function() {
		$caller.popover('destroy');
	}, timeout);
}

var testCheckBox = function(s) {
	if ($(s).is(':checked')) {
		return 'TRUE';
	} else {
		return 'FALSE';
	}
}

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
			$id.find('input[name=' + i + ']').change();
		}
	}
	cssPagedMedia.size($id.find('input[name=print_page_size]').val());
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
			function(data, textStatus, jqXHR) {
				if (data.success) {
					var $id = $('#config');
					fillInElement($id, data.element);

				} else {
					notify($('#config-save'), '', jqXHR.statusText, 'bg-danger', 4000);
				}
			}, 'json').fail(function() {
		notify($('#config-save'), '', 'Connection error', 'bg-danger', 4000);
	});
}

var saveConfig = function($id) {
	var elementVars = getElementValues($id);
	$.post(
			document.baseURI,
			'action=save_config&data=' + escape(JSON.stringify(elementVars)),
			function(data,textStatus,jqXHR) {
				if (data.success) {
					fillInElement($id, data.element);
					notify($('#config-save'), '', jqXHR.statusText, 'bg-success',
							2000);
				} else {
					notify($('#config-save'), '', jqXHR.statusText, 'bg-danger',
							4000);
				}
			}, 'json').fail(
			function() {
				notify($('#config-save'), '', 'Connection error', 'bg-danger',
						4000);
			});
}

var adaptLayout = function($id) {
	if ($id.is(':checkbox')) {
		toggleField($id);
	}
	var albumColumns = 0;
	$(
			'input[name=print_show_cover], ' + 'input[name=print_show_album_info], '
					+ 'input[name=print_show_tracks]').each(function() {
		if ($(this).prop('checked')) {
			albumColumns++;
		}
	});
	// adjust the width of the columns for each album
	var numCols = 12 / albumColumns << 0;
	var columnClass = 'col-xs-' + numCols;
	$('.cover').removeClass().addClass(columnClass + ' cover');
	$('.album-info').removeClass().addClass(columnClass + ' album-info');
	$('.tracks').removeClass().addClass(columnClass + ' tracks');

	// move around the album controls if necessary
	if ($('input[name=print_show_album_controls]').prop('checked')) {
		if ($('input[name=print_show_album_info]').prop('checked')) {
			attachAlbumControlsTo('.album-info');
			$('.album-controls').addClass('btn-group-justified');
		} else if ($('input[name=print_show_cover]').prop('checked')) {
			attachAlbumControlsTo('.cover');
			$('.album-controls').addClass('btn-group-justified');
		} else {
			attachAlbumControlsTo('.tracks');
			$('.album-controls').removeClass('btn-group-justified');
		}
	}

	// make sure we always see the power-on button
	if ($('input[name=print_show_cover]').prop('checked')) {
		attachPowerOnTo('.cover');
		$('.power-on').css('position', 'absolute');
		$('.power-on').removeClass('power-on-inline');
	} else if ($('input[name=print_show_album_info]').prop('checked')) {
		attachPowerOnTo('.album-info');
		$('.power-on').css('position', 'relative');
		$('.power-on').removeClass('power-on-inline');
	} else {
		attachPowerOnTo('.tracks');
		$('.power-on').css('position', 'relative');
		$('.power-on').addClass('power-on-inline');
	}
}

var attachAlbumControlsTo = function(selector) {
	$('.album').each(function() {
		if (selector === '.tracks') {
			$(this).find('.album-controls').prependTo($(this).find(selector));
		} else {
			$(this).find('.album-controls').appendTo($(this).find(selector));
		}
	});
}

var attachPowerOnTo = function(selector) {
	$('.album').each(function() {
		$(this).find('.power-on').prependTo($(this).find(selector));
	});
}

var toggleField = function($checkbox) {
	var selector = '.' + $checkbox.attr('name').slice(11).replace(/_/g, '-')
	if ($checkbox.prop('checked')) {
		$(selector).show();
	} else {
		$(selector).hide();
	}
}

var changeTileSize = function($id) {
	if ($id.val()) {
		var PPcm = 56.692845103;
		var size = $id.val() * PPcm;
		var column_sizes = [6, 4];
		$('.album').css({ 'min-width': size + 'px', 'min-height': size + 'px', 'max-width': size + 'px', 'max-height': size + 'px', 'overflow': 'hidden'});
		$('.album').find('.tracks').each(function(unused, tracks) {
		    resetTracks($(tracks).find('ul'));
		    var i = 0;
		    var $ul = $(tracks).find('ul');
		    while ($ul.prop('scrollHeight') > size - 156 && i < column_sizes.length ) {
		        $ul.find('li').removeClass().addClass('list-group-item col-xs-' + column_sizes[i++]);
		        $ul.find('.track-title').css({'overflow':'hidden', 'text-overflow': 'ellipsis', 'white-space': 'nowrap'});
		    }
		});
		/**
		 * TODO detect track ul overflow ( https://stackoverflow.com/questions/7138772/how-to-detect-overflow-in-div-element )
		 *      and increase number of columns as needed ( https://stackoverflow.com/questions/19836567/bootstrap-3-multi-column-within-a-single-ul-not-floating-properly )
		 */
	} else {
		$('.album').removeAttr('style');
        $('.album').find('.tracks').each(function(unused, tracks) {
            resetTracks($(tracks).find('ul'));
        });
	}
}

var resetTracks = function($ul) {
    $ul.removeClass('row');
    $ul.find('li').removeClass().addClass('list-group-item');
    $ul.find('.track-title').css({'overflow':'visible', 'text-overflow': 'clip', 'white-space': 'normal'});    
}

var changeNumberOfColumns = function($id) {
	if ($id.val() > 1) {
		var colWidth = 12 / $id.val() << 0;
		var columnClass = 'col-xs-' + colWidth;
		$('.album').parent().removeClass().addClass(columnClass);
		$('.album').parent().appendTo('#wrap-all-print');
		$('.album-row').remove();
		var rowHTML = '<div class="row album-row"></div>';
		var rowCount = 0;
		$('.album').parent().each( function(albumCount){
			if ( (albumCount % $id.val()) === 0 ) {
				rowCount++;
				$('#wrap-all-print').append('<div id="row-' + rowCount + '" class="row album-row"></div>');
			}
			$(this).appendTo('#row-' + rowCount);
		});
		$('#general-controls').appendTo('#wrap-all-print');
	} else {
		$('.album').parent().removeClass().addClass('row');
		$('.album').parent().appendTo('#wrap-all-print');
		$('.album-row').remove();
		$('#general-controls').appendTo('#wrap-all-print');
	}
}

var savePDF = function() {
	$.post(
			document.baseURI,
			'action=save_pdf&data=' + escape(JSON.stringify({content: $('#wrap-all-print').html()})),
			function(data,textStatus,jqXHR) {
				if (data.success) {
					setTimeout(function() { window.open('/print.pdf'); }, 10000);
					notify($('#pdf-save'), '', 'Creating pdf, please wait about 10 s... (you need to allow popups to see the pdf. otherwise open "http://'+window.location.host+'/print.pdf" manually', 'bg-info',
							10000);
				} else {
					notify($('#pdf-save'), '', jqXHR.statusText, 'bg-danger',
							4000);
				}
			}, 'json').fail(
			function() {
				notify($('#pdf-save'), '', 'Connection error', 'bg-danger',
						4000);
			});
	
}

$(function() {
	// fetch the configuration from the database
	getConfig();
	
	tileStyle = (function() {
		// Create the <style> tag
		var style = document.createElement("style");
		// WebKit hack :(
		style.appendChild(document.createTextNode(""));
		// Add the <style> element to the page
		document.getElementById('wrap-all-print').appendChild(style);
		return style.sheet;
	})();
	// save visible layout as pdf
	$('#pdf-save').click(function(){
		savePDF();
	});

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
	$('#list').click(function() {
		selectPreset('list');
	});
	$('#tiles').click(function() {
		selectPreset('tiles');
	});
	$('#cd').click(function() {
		selectPreset('cd');
	});

	// Change page media size if option is changed
	$('input[name=page_size]').change(function() {
		cssPagedMedia.size($(this).val());
	});
	// change print layout according to layout options
	$(
			'input[name=print_show_cover], ' + 'input[name=print_show_album_info], '
					+ 'input[name=print_preset], ' + 'input[name=print_show_album_controls], '
					+ 'input[name=print_show_tracks]').change(function() {
		adaptLayout($(this));
	});
	$('input[name=print_show_general_controls]').change(function() {
		toggleField($(this));
	});
	$('input[name=print_num_cols]').change(function() {
		changeNumberOfColumns($(this));
	});
	$('input[name=print_tile_size]').change(function() {
		changeTileSize($(this));
	});
});
