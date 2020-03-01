// Call the dataTables jQuery plugin
jQuery(document).ready(function() {
	jQuery('#dataTable').DataTable();

	jQuery('table.pokemons-list tbody').infiniteScroll({
		path: '.pagination-next',
		append: 'table.pokemons-list tbody tr',
		/*history: 'push', */
		hideNav: '.pagination',
		status: '.page-load-status'
	});
});