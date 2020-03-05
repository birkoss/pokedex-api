jQuery(document).ready(function() {

	jQuery("#pokemon-modal .btn-save").click(function() {
		/* Do NOT allow saving while it's already in process */
		if (jQuery("#pokemon-modal .btn-save").prop("disabled")) {
			return;
		}
		jQuery("#pokemon-modal .btn-save").prop("disabled", true).html("Saving...");

		/* Fetch all options from the modal */
		var options = {};
		jQuery("#pokemon-modal input[type='checkbox']").each(function() {
			options[ jQuery(this).attr("id") ] = jQuery(this).prop("checked");
		});

		var pokemon_number = jQuery("#pokemon-modal input[name='pokemon_number']").val();

		/* Update all options for this pokemon */
		pokemon_toggle_options(pokemon_number, options, function(ret) {
			jQuery("#pokemon-modal .btn-save").prop("disabled", false).html("Save");
			jQuery('#pokemon-modal').modal('hide');

			if (options['is_owned'] != undefined) {
				if (options['is_owned']) {
					jQuery(".container-pokemon-" + pokemon_number + " a.pokemon-sprite").addClass("is-owned");
				} else {
					jQuery(".container-pokemon-" + pokemon_number + " a.pokemon-sprite").removeClass("is-owned");
				}
			}
		});
	});

	jQuery.ajax({
		'type': "GET",
		'url': ajax_first_page,
		'data': {
			
		},
		success: function(ret) {
			jQuery(".pokemons-grid").html(ret);

			jQuery('.pokemons-grid').infiniteScroll({
				path: '.pagination-next',
				append: '.card.pokemon',
				//history: 'push',
				hideNav: '.pagination',
				status: '.page-load-status'
			});
		}
	});
});

function pokemon_change_option(pokemon_number, option_name) {
	jQuery(".container-pokemon-" + pokemon_number + " td.actions > .btn-mark-owned").hide();
	jQuery(".container-pokemon-" + pokemon_number + " td.actions").prepend('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" style="display: block; shape-rendering: auto;" width="60px" height="60px" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid"><circle cx="59.6265" cy="50" fill="#e83a38" r="20"><animate attributeName="cx" repeatCount="indefinite" dur="1s" keyTimes="0;0.5;1" values="30;70;30" begin="-0.5s"></animate></circle><circle cx="40.3735" cy="50" fill="#4c4b49" r="20"><animate attributeName="cx" repeatCount="indefinite" dur="1s" keyTimes="0;0.5;1" values="30;70;30" begin="0s"></animate></circle><circle cx="59.6265" cy="50" fill="#e83a38" r="20"><animate attributeName="cx" repeatCount="indefinite" dur="1s" keyTimes="0;0.5;1" values="30;70;30" begin="-0.5s"></animate><animate attributeName="fill-opacity" values="0;0;1;1" calcMode="discrete" keyTimes="0;0.499;0.5;1" dur="1s" repeatCount="indefinite"></animate></circle></svg>');

	var options = {};
	options[option_name] = -1;

	pokemon_toggle_options(pokemon_number, options, function(ret) {
		if (ret['status'] == "ok") {
			jQuery(".container-pokemon-" + pokemon_number + " td.actions svg").remove();
			jQuery(".container-pokemon-" + pokemon_number + " td.actions > .btn-options").show();
		}
	});
}

function pokemon_show_modal(pokemon_number) {
	jQuery('#pokemon-modal .modal-body').load(ajax_single_option.replace("0000", pokemon_number), function() {
		jQuery('#pokemon-modal').modal({show:true});
	});
}

function pokemon_toggle_options(pokemon_number, options, callback) {
	jQuery.ajax({
		type: "POST",
		url: ajax_single_option.replace("0000", pokemon_number),
		data: {
			"options": JSON.stringify(options),
			"csrfmiddlewaretoken": ajax_csrf_token
		},
		success: function(ret) {
			if (callback != undefined) {
				callback(ret);
			}
		}
	});
}