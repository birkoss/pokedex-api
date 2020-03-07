/* Use to keep the existing Modal Options when it's first open */
var ORIGINAL_MODAL_OPTIONS = {};
var POKEMON_FILTERS = ["is_owned", "is_shiny", "is_pokeball", "is_language", "is_iv", "is_original_trainer", "is_gender"];


/* Load the options for this pokemon and show the modal */
function pokemon_show_modal(pokemon_number) {
	jQuery('#pokemon-modal .modal-body').load(AJAX_SINGLE_OPTION.replace("0000", pokemon_number), function() {
		jQuery('#pokemon-modal').modal({show:true});
		jQuery('[data-toggle="tooltip"]').tooltip();
		jQuery("#pokemon-modal .btn-save").prop("disabled", true);

		ORIGINAL_MODAL_OPTIONS = JSON.stringify(get_modal_options());

		/* Activate/Disable the SAVE button when options are changed */
		jQuery("#pokemon-modal input[type='checkbox']").change(function() {
			var current_modal_options = JSON.stringify(get_modal_options());

			jQuery("#pokemon-modal .btn-save").prop("disabled", (ORIGINAL_MODAL_OPTIONS == current_modal_options));
		});
	});

	return false;
}


/* Save the options for this Pokemon */
function pokemon_save_options(pokemon_number, options, callback) {
	jQuery.ajax({
		type: "POST",
		url: AJAX_SINGLE_OPTION.replace("0000", pokemon_number),
		data: {
			"options": JSON.stringify(options),
			"csrfmiddlewaretoken": AJAX_CSRF_TOKEN
		},
		success: function(ret) {
			if (callback != undefined) {
				callback(ret);
			}
		}
	});
}


/* Get all the options (name and value) from the modal */
function get_modal_options() {
	modal_options = {};
	jQuery("#pokemon-modal input[type='checkbox']").each(function() {
		modal_options[ jQuery(this).attr("id") ] = jQuery(this).prop("checked");
	});
	return modal_options;
}


/* Update a filter (add or remove depending on if it's present */
function update_filter(name, value) {

	jQuery.ajax({
		type: "POST",
		url: AJAX_FILTER,
		data: {
			type: name,
			value: value,
			"csrfmiddlewaretoken": AJAX_CSRF_TOKEN
		},
		success: function(ret) {
			console.log(ret);
		}
	})

	return false;
}

jQuery(document).ready(function() {
	/* Bind the SAVE button in the modal */
	jQuery("#pokemon-modal .btn-save").click(function() {
		/* Do NOT allow saving while it's already in process */
		if (jQuery("#pokemon-modal .btn-save").prop("disabled")) {
			return;
		}
		jQuery("#pokemon-modal .btn-save").prop("disabled", true).html("Saving...");

		/* Fetch all options from the modal */
		var options = get_modal_options();

		var pokemon_number = jQuery("#pokemon-modal input[name='pokemon_number']").val();

		/* Update all options for this pokemon */
		pokemon_save_options(pokemon_number, options, function(ret) {
			jQuery("#pokemon-modal .btn-save").prop("disabled", false).html("Save");
			jQuery('#pokemon-modal').modal('hide');

			/* Activate the filter in the Pokemon card */
			POKEMON_FILTERS.forEach(function(single_filter) {
				if (options[single_filter] != undefined) {
					if (options[single_filter]) {
						jQuery(".container-pokemon-" + pokemon_number).addClass(single_filter.replace("_", "-"));
					} else {
						jQuery(".container-pokemon-" + pokemon_number).removeClass(single_filter.replace("_", "-"));
					}
				}
			});
		});
	});

	/* Load the first Pokemon page */
	if (jQuery(".main-pokemons-list").length) {
		jQuery.ajax({
			'type': "GET",
			'url': AJAX_FIRST_PAGE,
			'data': {
				"type": AJAX_POKEMON_TYPE
			},
			success: function(ret) {
				jQuery(".pokemons-grid").html(ret);

				if (jQuery(".pagination-next").length) {
					jQuery('.pokemons-grid').infiniteScroll({
						path: '.pagination-next',
						append: '.card.pokemon',
						//history: 'push',
						history: 'none',
						hideNav: '.pagination',
						status: '.page-load-status'
					});
				}
			}
		});
	}
});