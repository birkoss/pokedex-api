// Call the dataTables jQuery plugin
jQuery(document).ready(function() {
	jQuery('body.logged-in #pokemons-list').DataTable();

	jQuery('body:not(.logged-in) table.pokemons-list tbody').infiniteScroll({
		path: '.pagination-next',
		append: 'table.pokemons-list tbody tr',
		//history: 'push',
		hideNav: '.pagination',
		status: '.page-load-status'
	});

});

function pokemon_change_option(pokemon_number, option_name) {
	jQuery.ajax({
		type: "POST",
		url: "/pokemon/" + pokemon_number + "/toggle",
		data: {
			"option": option_name,
			"csrfmiddlewaretoken": ajax_csrf_token
		},
		success: function(ret) {
			console.log(ret);
		}
	});
}