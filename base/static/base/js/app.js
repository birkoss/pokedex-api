/* Use to keep the existing Modal Options when it's first open */
var ORIGINAL_MODAL_OPTIONS = {};

/* All the filters available in the apps */
var POKEMON_FILTERS = {
	"is_owned": {
		"name": "Owned",
		"help": "Do you have this pokemon?",
		"icon": "fas fa-check"
	}, 
	"is_shiny": {
		"name": "Shiny",
		"help": "Do you have this pokemon as a shiny?",
		"icon": "fas fa-star"
	}, 
	"is_pokeball": {
		"name": "Pokeball",
		"help": "Do you have this pokemon in the correct Pokeball?",
		"icon": "fas fa-dot-circle"
	}, 
	"is_language": {
		"name": "Language",
		"help": "Does this Pokemon is from the correct language?",
		"icon": "fas fa-language"
	}, 
	"is_iv": {
		"name": "IV",
		"help": "Does this Pokemon have the correct IVs?",
		"icon": "fas fa-dumbbell"
	}, 
	"is_original_trainer": {
		"name": "Original Trainer",
		"help": "Are you are the Original Trainer?",
		"icon": "fas fa-user"
	}, 
	"is_gender": {
		"name": "Gender",
		"help": "Does this Pokemon has correct gender?",
		"icon": "fas fa-venus-mars"
	}
};

var INFINITE_SCROLL = null;


function change_language(new_language) {
	jQuery.ajax({
		type: "POST",
		url: AJAX_FILTERS,
		data: {
			type: "language",
			value: new_language,
			"csrfmiddlewaretoken": AJAX_CSRF_TOKEN
		},
		success: function(ret) {
			ajax_refresh_pokemons();
		}
	});
}


/* Get all the options (name and value) from the modal */
function modal_get_options() {
	modal_options = {};
	jQuery("#app-modal input[type='checkbox']").each(function() {
		modal_options[ jQuery(this).attr("id") ] = jQuery(this).prop("checked");
	});
	return modal_options;
}


/* Load the filters for the app and show the modal */
function modal_show_options() {
	jQuery('#app-modal .modal-body').load(AJAX_FILTERS, function() {

		Object.keys(POKEMON_FILTERS).forEach(function(single_filter) {
			jQuery(".pokemon-options").append('<div class="form-group form-check"><div class=""><input class="form-check-input" type="checkbox" id="' + single_filter + '" /><label class="form-check-label" for="' + single_filter + '" data-toggle="tooltip" data-placement="top">' + POKEMON_FILTERS[single_filter]['name'] + ' <i class="' + POKEMON_FILTERS[single_filter]['icon'] + '"></i></label></div></div>');
		});

		/* Get the current options in the modal */
		try {
			var modal_options = jQuery("#app-modal .pokemon-options").data("options").replace(/'/g, '"');

			/* Check the options */
			current_options = JSON.parse(modal_options);
			JSON.parse(modal_options).forEach(function(single_option) {
				jQuery("#app-modal #" + single_option).prop("checked", true);
			});
		} catch(err) {
			/* @TODO: Add a warning to prevent the user the options were not loaded correctly */
		}

		ORIGINAL_MODAL_OPTIONS = JSON.stringify(modal_get_options());

		jQuery("#app-modal input[type='checkbox']").change(function() {
			/* Disable/enable the SAVE button if the filters are not the same as the original filters the modal had */
			var current_modal_options = JSON.stringify(modal_get_options());
			jQuery("#app-modal .btn-save").prop("disabled", (ORIGINAL_MODAL_OPTIONS == current_modal_options));
		});

		jQuery('#app-modal .modal-title').html("Filters");
		jQuery('#app-modal').modal({show:true});
		jQuery('[data-toggle="tooltip"]').tooltip();
		jQuery("#app-modal .btn-save").prop("disabled", true);

		/* Bind the SAVE button in the modal */
		jQuery("#app-modal .btn-save").unbind("click").click(function() {
			/* Do NOT allow saving while it's already in process */
			if (jQuery("#app-modal .btn-save").prop("disabled")) {
				return;
			}
			jQuery("#app-modal .btn-save").prop("disabled", true).html("Saving...");

			var all_filters = modal_get_options();

			/* Get only the checked filters to save them */
			var new_filters = [];
			for (var single_option in all_filters) {
				if (all_filters[single_option]) {
					new_filters.push(single_option);
				}
			}


			/* Save checked filters */
			ajax_save_options(new_filters, function(ret) {
				if (ret['status'] == "ok") {
					jQuery("#app-modal .btn-save").prop("disabled", false).html("Save");
					jQuery('#app-modal').modal('hide');

					ajax_refresh_pokemons();
				}
			});

		});
	});

	return false;
}


/* Load the options for this pokemon and show the modal */
function modal_show_pokemon_options(pokemon_number) {
	jQuery('#app-modal .modal-body').load(AJAX_SINGLE_OPTION.replace("0000", pokemon_number), function() {

		/* Create all options in the modal */
		Object.keys(POKEMON_FILTERS).forEach(function(single_filter) {		
			jQuery("#app-modal .pokemon-options").append('<div class="form-group form-check"><div class=""><input class="form-check-input" type="checkbox" id="' + single_filter + '" /><label class="form-check-label" for="' + single_filter + '" data-toggle="tooltip" title="' + POKEMON_FILTERS[single_filter]['help'] + '" data-placement="top">' + POKEMON_FILTERS[single_filter]['name'] + ' <i class="' + POKEMON_FILTERS[single_filter]['icon'] + '"></i></label></div></div>');
		});

		/* Get the current options in the modal */
		try {
			var modal_options = jQuery("#app-modal .pokemon-options").data("options").replace(/'/g, '"');

			/* Check the options */
			current_options = JSON.parse(modal_options);
			JSON.parse(modal_options).forEach(function(single_option) {
				jQuery("#app-modal #" + single_option).prop("checked", true);
			});
		} catch(err) {
			/* @TODO: Add a warning to prevent the user the options were not loaded correctly */
		}

		jQuery('#app-modal .modal-title').html("Options");
		jQuery('#app-modal').modal({show:true});
		jQuery('#app-modal [data-toggle="tooltip"]').tooltip();
		jQuery("#app-modal .btn-save").prop("disabled", true);

		/* Update filters if the is_owned is checked */
		modal_options_update_state(jQuery("#is_owned").prop("checked"));

		/* Save the original options */
		ORIGINAL_MODAL_OPTIONS = JSON.stringify(modal_get_options());

		/* Activate/Disable the SAVE button when options are changed */
		jQuery("#app-modal input[type='checkbox']").change(function() {
			/* If the is_owned filter is changed, we disable/enable the other filters */
			var filter_id = jQuery(this).attr("id");
			if (filter_id == "is_owned") {
				modal_options_update_state(jQuery(this).prop("checked"));
			}

			/* Disable/enable the SAVE button if the filters are not the same as the original filters the modal had */
			var current_modal_options = JSON.stringify(modal_get_options());
			jQuery("#app-modal .btn-save").prop("disabled", (ORIGINAL_MODAL_OPTIONS == current_modal_options));
		});

		/* Bind the SAVE button in the modal */
		jQuery("#app-modal .btn-save").unbind("click").click(function() {
			/* Do NOT allow saving while it's already in process */
			if (jQuery("#app-modal .btn-save").prop("disabled")) {
				return;
			}
			jQuery("#app-modal .btn-save").prop("disabled", true).html("Saving...");

			/* Fetch all options from the modal */
			var options = modal_get_options();

			var pokemon_number = jQuery("#app-modal .pokemon-options").data("pokemon-number");

			/* Update all options for this pokemon */
			ajax_save_pokemon_options(pokemon_number, options, function(ret) {
				jQuery("#app-modal .btn-save").prop("disabled", false).html("Save");
				jQuery('#app-modal').modal('hide');

				/* Activate the filter in the Pokemon card */
				Object.keys(POKEMON_FILTERS).forEach(function(single_filter) {
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
	});
	return false;
}


/* Disable/enable the other filters depending if is_owned is checked or not */
function modal_options_update_state(is_owned_checked) {
	if (is_owned_checked) {
		/* Enable all other filters */
		Object.keys(POKEMON_FILTERS).forEach(function(single_filter) {
			if (single_filter != "is_owned") {
				jQuery("#" + single_filter).prop("disabled", false);
			}
		});
	} else {
		/* Disable and uncheck all other filters */
		Object.keys(POKEMON_FILTERS).forEach(function(single_filter) {
			if (single_filter != "is_owned") {
				jQuery("#" + single_filter).prop("checked", false).prop("disabled", true);
			}
		});
	}
}


/* Clear the filters */
function status_clear_filters() {
	ajax_save_options([], function(ret) {
		if (ret['status'] == "ok") {
			ajax_refresh_pokemons();
		}
	});
}


/* Update the pokedex status depending on the user data */
function status_update_pokedex_stats(pokedex_stats) {
	var content = "";

	if (pokedex_stats['anonymous'] == 1) {
		/* Unlogged status, only the total */
		content = pokedex_stats['total'] + " Pokemon(s)";
	} else {
		/* Logged user without HIDE filter */
		if (pokedex_stats['hide'] == 0) {
			content = "Remaining: " + (pokedex_stats['total']-pokedex_stats['count_is_owned']) + " / " + pokedex_stats['total'] + " Pokemon(s)";
		} else {
			content = "Remaining: " + pokedex_stats['current'] + " / " + pokedex_stats['total'] + " Pokemon(s)";
		}
	}

	jQuery(".total-pokemons-status").html(content).show();
}


/* Update the filters */
function status_update_filters(filters) {
	var content = "";

	if (filters.length > 0) {
		content += "Filters: ";
		filters.forEach(function(single_filter) {
			if (POKEMON_FILTERS[single_filter]) {
				content += '<i class="' + POKEMON_FILTERS[single_filter]['icon'] + '"></i> ' + POKEMON_FILTERS[single_filter]['name'] + " ";
			}
		});
		content += ' <a href="#" onclick="return status_clear_filters();">Reset</a>';
	}

	jQuery(".content-header .filters").html(content);
	if (content == "") {
		jQuery(".content-header .filters").hide();
	} else {
		jQuery(".content-header .filters").show();
	}
}


/* Load the Pokemons list first page */
function ajax_refresh_pokemons() {
	jQuery.ajax({
		"type": "GET",
		"url": AJAX_FIRST_PAGE,
		success: function(ret) {
			jQuery(".pokemons-grid").html(ret['content']);

			/* Update and show the total */
			status_update_pokedex_stats(ret['pokedex_stats']);

			/* Update and show the filters status (if any) */
			status_update_filters(ret['filters_status']);

			/* Update language in the dropdown */
			jQuery(".dropdown-language .fa-check").hide();
			jQuery(".dropdown-language .lang-" + ret['pokemon_language'] + " .fa-check").show();

			/* Setup the infinite scroll if any pagination is present */
			if (jQuery(".pagination-next").length) {
				if (INFINITE_SCROLL != null) {
					jQuery('.pokemons-grid').infiniteScroll("destroy");
					INFINITE_SCROLL = null;
				}
				INFINITE_SCROLL = jQuery('.pokemons-grid').infiniteScroll({
					path: '.pagination-next',
					append: '.card.pokemon',
					history: 'none',
					hideNav: '.pagination',
					status: '.page-load-status'
				});
			}
		}
	});
}


/* Save the options for this Pokemon */
function ajax_save_pokemon_options(pokemon_number, options, callback) {
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


/* Save the options */
function ajax_save_options(options, callback) {
	jQuery.ajax({
		type: "POST",
		url: AJAX_FILTERS,
		data: {
			type: "hide",
			values: options,
			"csrfmiddlewaretoken": AJAX_CSRF_TOKEN
		},
		success: function(ret) {
			if (callback != undefined) {
				callback(ret);
			}
		}
	});
}


jQuery(document).ready(function() {
	/* Load the first Pokemon page */
	if (jQuery(".main-pokemons-list").length) {
		ajax_refresh_pokemons();
	}
});