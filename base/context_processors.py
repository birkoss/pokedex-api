from django.db import connection


def queries_processor(request):
	#queries = connection.queries
	return {
		'queries': ["aa"]
	}