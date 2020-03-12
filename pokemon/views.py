from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import connection
from django.db.models import FilteredRelation, Q, Count, Case, When, Value
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string

import urllib.request
import json
import math
from urllib.request import urlopen, Request

from pokemon.models import Pokemon, Region, Generation, UserPokemon, PokemonRegion

from project.settings import MODELTRANSLATION_LANGUAGES


@login_required
def pokemon_options(request, pokemon_number):
	if request.method == "GET":
		request_header_requested_with = request.META.get("HTTP_X_REQUESTED_WITH", "")

		if request_header_requested_with != "XMLHttpRequest":
			return redirect('pokemon_archive')

		pokemon = Pokemon.objects.filter(number=pokemon_number).first()

		current_options = []

		# Get all enabled options for this pokemon and this user
		pokemon_options = UserPokemon.objects.filter(pokemon=pokemon, user=request.user).first()
		if pokemon_options != None:
			for single_field in pokemon_options._meta.get_fields():
				if single_field.name[0:3] == "is_" and getattr(pokemon_options, single_field.name) == True:
					current_options.append(single_field.name)

		return render(request, "pokemon/modal_options.html", {
			'pokemon': pokemon,
			'current_options': current_options,
			'current_options_json': json.dumps(current_options)
		})

	if request.method == "POST":
		response = {
			"status": "pending"
		}

		# Must parse a valid JSON from $_POST['options']
		try:
			options = json.loads(request.POST.get("options"))
		except json.decoder.JSONDecodeError:
			response['status'] = "error"
			response['msg'] = "Invalid options!"
			return JsonResponse(response)			

		# Must have at least ONE valid
		if len(options) == 0:
			response['status'] = "error"
			response['msg'] = "You must specific at least one option!"
			return JsonResponse(response)

		# Must be logged in first
		if not request.user.is_authenticated:
			response['status'] = "error"
			response['msg'] = "You must be logged in!"
			return JsonResponse(response)

		# Must be a valid Pokemon from $_GET['pokemon_number']
		pokemon = Pokemon.objects.filter(number=pokemon_number).first()
		if pokemon is None:
			response['status'] = "error"
			response['msg'] = "This pokemon doesn't exist!"
			return JsonResponse(response)

		# Get the existing UserPokemon for this user and pokemon if possible, else create it
		pokemon_options = UserPokemon.objects.filter(pokemon=pokemon, user=request.user).first()
		if pokemon_options is None:
			pokemon_options = UserPokemon(pokemon=pokemon, user=request.user)
			pokemon_options.save()

		# Try to update each options, they must all be valid
		for option_name in options:
			try:
				option_new_value = options[option_name]
				option_existing_value = getattr(pokemon_options, option_name)

				# -1 means to toggle the existing value
				if option_new_value == -1:
					option_new_value = not option_existing_value

				setattr(pokemon_options, option_name, option_new_value)
			except AttributeError:
				response['status'] = "error"
				response['msg'] = "This option " + option_name + " doesn't exist!"
				return JsonResponse(response)

		pokemon_options.save();

		print(connection.queries)

		response['status'] = "ok"

		return JsonResponse(response)


def pokemon_archive(request):
	return render(request, "pokemon/archive.html", {
		"page_url": "pokemon_archive_page",
		"page_title": "National Pokedex"
	})


def pokemon_forms_archive(request):
	return render(request, "pokemon/archive.html", {
		"page_url": "pokemon_forms_archive_page",
		"page_title": "Alternate Forms"
	})


def pokemon_pokedex_archive(request, region=None):
	single_region = Region.objects.filter(slug=region).first()

	if single_region == None:
		redirect('pokemon_archive')

	return render(request, "pokemon/archive.html", {
		"page_url": "pokemon_pokedex_archive_page",
		"region": region,
		"page_title": "Pokemons from " + single_region.name
	})


def pokemon_pokedex_archive_page(request, region=None, page=1):
	request_header_requested_with = request.META.get("HTTP_X_REQUESTED_WITH", "")
	if request_header_requested_with != "XMLHttpRequest":
		return redirect('pokemon_pokedex_archive', region=region)

	page_content = fetch_page(request, page, 'pokemon_pokedex_archive_page', **{'pokemon_region':region})

	if page == 1:
		return JsonResponse(page_content)
	else:
		return HttpResponse(page_content['content'])


def pokemon_archive_page(request, page=1):
	request_header_requested_with = request.META.get("HTTP_X_REQUESTED_WITH", "")
	if request_header_requested_with != "XMLHttpRequest":
		return redirect('pokemon_archive')

	page_content = fetch_page(request, page, 'pokemon_archive_page', **{'pokemon_type':"pokemons"})

	if page == 1:
		return JsonResponse(page_content)
	else:
		return HttpResponse(page_content['content'])


def pokemon_forms_archive_page(request, page=1):
	request_header_requested_with = request.META.get("HTTP_X_REQUESTED_WITH", "")
	if request_header_requested_with != "XMLHttpRequest":
		return redirect('pokemon_forms_archive')

	page_content = fetch_page(request, page, 'pokemon_forms_archive_page', **{'pokemon_type':"forms"})

	if page == 1:
		return JsonResponse(page_content)
	else:
		return HttpResponse(page_content['content'])


# @TODO : Merge pokemons_cards with pokemon_detail
def pokemon_single(request, pokemon_number=None):
	pokemons_data = fetch_pokemons(user=request.user, pokemon_number=pokemon_number)
	
	if len(pokemons_data['pokemons']) != 1:
		raise Http404

	if pokemons_data['pokemons'][0]['variant__number'] == None:
		variants_data = fetch_pokemons(user=request.user, variant__number=pokemon_number)
	else:
		variants_data = fetch_pokemons(user=request.user, pokemon_number=pokemons_data['pokemons'][0]['variant__number'])

	regions = PokemonRegion.objects.filter(pokemon__number=pokemons_data['pokemons'][0]['number']).select_related("region")

	return render(request, "pokemon/single.html", {
		'pokemon': pokemons_data['pokemons'][0],
		'variants': variants_data['pokemons'],
		"regions": regions
	})


def import_pokemon(request):
	headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'}

	import_names = True
	import_forms = True
	import_regions = True

	# Import Pokemons from their names
	if import_names:
		json_url = "https://birkoss.com/pokemon_names.json"
		r = Request(url=json_url, headers=headers)
		with urllib.request.urlopen(r) as url:
			pokemons = json.loads(url.read().decode())
			for national_number in pokemons:
				pokemon = Pokemon.objects.filter(number=national_number)
				if len(pokemon) == 0:
					data = {}
					data['number'] = national_number
					for mlid in ('names/en', 'names/fr', 'names/jp', 'names/de', 'names/kr'):
						if mlid in pokemons[national_number]:
							data[mlid.replace("s/", "_")] = pokemons[national_number][mlid]

					# Create the new Pokemon
					pokemon = Pokemon(**data)
					pokemon.save()
					print("Created Pokemon: " + national_number)

	# Import Forms
	if import_forms:
		json_url = "https://birkoss.com/pokemon_forms.json"
		r = Request(url=json_url, headers=headers)

		with urllib.request.urlopen(r) as url:
			pokemons = json.loads(url.read().decode())
			for single_pokemon in pokemons:
				pokemon = Pokemon.objects.filter(number=single_pokemon['number'])
				if len(pokemon) == 0:
					data = {}
					data['number'] = single_pokemon['number']
					data['variant'] = Pokemon.objects.filter(number=single_pokemon['national']).first()
					for mlid in ('names/en', 'names/fr', 'names/jp', 'names/de', 'names/kr'):
						if mlid in single_pokemon:
							data[mlid.replace("s/", "_")] = single_pokemon[mlid]

					# Create the new Forms
					pokemon = Pokemon(**data)
					pokemon.save();
					print("Created Form: " + single_pokemon['number'])

	if import_regions:
		json_url = "https://birkoss.com/pokemon_regions.json"
		r = Request(url=json_url, headers=headers)

		with urllib.request.urlopen(r) as url:
			regions = json.loads(url.read().decode())
			for single_region in regions:
				region = Region.objects.filter(slug=single_region).first()
				print(region)
				if region != None:
					for single_pokemon in regions[single_region]:
						pokemon = Pokemon.objects.filter(number=single_pokemon['national']).first()
						if pokemon != None:
							pokemon_region = PokemonRegion.objects.filter(pokemon=pokemon, region=region).first()
							if pokemon_region == None:
								pokemon_region = PokemonRegion(pokemon=pokemon, region=region, number=single_pokemon['regional'])
								pokemon_region.save()
								print("Created regional: " + single_region + " #" + single_pokemon['regional'])
					

	return HttpResponse("<p>Done</p>")


def fetch_pokemons(**kwargs):

	# Those totals = current / total
	pokedex_stats = {
		'current': 0,
		'total': 0,
		'filters': 0,
		'anonymous': 1
	}

	# @TODO: Remove hardcoding and make it dynamic from the model
	pokemon_filters = ("is_owned", "is_shiny", "is_pokeball", "is_language", "is_iv", "is_original_trainer", "is_gender")

	pagination = 40

	qs_annotate = {}
	qs_values = ["name", "number", "variant__name", "variant__number"]

	qs_filters = Q()
	qs_filters_hidden = Q()

	qs_order_by = "number"

	# Dynamically add language for name and variant
	for single_language in MODELTRANSLATION_LANGUAGES:
		qs_values.append("name_" + single_language)
		qs_values.append("variant__name_" + single_language)

	if "pokemon_region" in kwargs and kwargs['pokemon_region'] != "":
		qs_filters.add(Q(pokemonregion__region__slug=kwargs['pokemon_region']), Q.AND)
		qs_values.append("pokemonregion__number")
		qs_order_by = "pokemonregion__number"

	if "pokemon_type" in kwargs:
		if kwargs['pokemon_type'] == "pokemons":
			qs_filters.add(Q(variant__isnull=True), Q.AND)
		elif kwargs['pokemon_type'] == "forms":
			qs_filters.add(Q(variant__isnull=False), Q.AND)

	if "pokemon_number" in kwargs:
		qs_filters.add(Q(number=kwargs['pokemon_number']), Q.AND)

	if "variant__number" in kwargs:
		qs_filters.add(Q(variant__number=kwargs['variant__number']), Q.AND)

	# If logged in, left join with the UserPokemon data of that user
	if "user" in kwargs and kwargs['user'].is_authenticated:
		for single_filter in pokemon_filters:
			qs_values.append("t__" + single_filter)

		qs_annotate['t'] = FilteredRelation(
			'userpokemon', condition=(Q(userpokemon__user=kwargs['user']) | Q(userpokemon__isnull=True))
		)

		# Apply search
		if "search_text" in kwargs and kwargs['search_text'] != "":
			search_number = kwargs['search_text']

			# Pad the number lower than 100 to be like our number : 1 -> 001
			if len(search_number) < 3:
				search_number = search_number.zfill(3)

			qs_search = Q()
			if "pokemon_region" in kwargs and kwargs['pokemon_region'] != "":
				qs_search.add(Q(**{'pokemonregion__number':search_number}), Q.OR)
			else:
				qs_search.add(Q(**{'number':search_number}), Q.OR)

			for single_language in MODELTRANSLATION_LANGUAGES:
				qs_search.add(Q(**{'name_'+single_language+'__contains':kwargs['search_text']}), Q.OR)

			qs_filters.add(qs_search, Q.AND)

		# Apply settings filters
		if "settings_filters" in kwargs and len(kwargs['settings_filters']) > 0:
			pokedex_stats['filters'] = 1
			for single_filter in kwargs['settings_filters']:
				qs_filters_hidden.add(Q(**{'t__' + single_filter:False}) | Q(userpokemon__isnull=True), Q.AND)


	# Get the Pokemons depending on all the differents settings
	pokemons_qs = get_pokemon_queryset(qs_annotate, (qs_filters & qs_filters_hidden), qs_values, qs_order_by)


	# Pagination
	pokemons_paginator = None
	if "page" in kwargs and kwargs['page'] != None:
		paginator = Paginator(pokemons_qs, pagination)
		pokedex_stats['current'] = paginator.count
		pokedex_stats['total'] = paginator.count
		try:
			pokemons_paginator = paginator.page(kwargs['page'])
		except PageNotAnInteger:
			pokemons_paginator = paginator.page(1)
		except EmptyPage:
			pokemons_paginator = paginator.page(paginator.num_pages)
	else:
		pokemons_paginator = pokemons_qs
		pokedex_stats['current'] = len(pokemons_qs)

	pokemons_list = []
	for single_pokemon in pokemons_paginator:
		pokemon = single_pokemon
		pokemon['visible_number'] = pokemon['number'][:3]

		if 'pokemon_language' in kwargs and kwargs['pokemon_language'] != "en":
			translated_name = pokemon['name_' + kwargs['pokemon_language']]
			if translated_name != "":
				pokemon['name'] = translated_name

		if 'pokemonregion__number' in single_pokemon and single_pokemon['pokemonregion__number'] != None:
			pokemon['visible_number'] = single_pokemon['pokemonregion__number'][:3]

		if single_pokemon['variant__name'] != None:
			variant_name = single_pokemon['variant__name']
			if 'pokemon_language' in kwargs and kwargs['pokemon_language'] != "en":
				translated_name = pokemon['variant__name_' + kwargs['pokemon_language']]
				if translated_name != "":
					variant_name = translated_name
			pokemon['name'] = single_pokemon['name'].replace("#NAME#", variant_name)

		# Init filters to default values
		for single_filter in pokemon_filters:
			pokemon[ single_filter ] = None

			# Update the filter in they are found in the database
			if "t__" + single_filter in single_pokemon:
				pokemon[ single_filter ] = single_pokemon["t__" + single_filter]

		pokemons_list.append(pokemon)

	# If the user is logged in, get the total of filters
	if "user" in kwargs and kwargs['user'].is_authenticated:
		# Will hold the number of Pokemons matching all those filters (except filtered one)
		qs_aggregate = {
			'total_pokemons': Count('id', distinct=True)
		}

		# Add all the count of the filters 
		for single_filter in pokemon_filters:
			qs_aggregate['count_' + single_filter] = Count(Case(When(**{'userpokemon__'+single_filter: True}, then=Value(1))))


		pokemons_total_qs = get_pokemon_queryset(qs_annotate, qs_filters, qs_values, qs_order_by).aggregate(
			**qs_aggregate
		)

		# Get all the values (from filters and the total)
		pokedex_stats['anonymous'] = 0
		pokedex_stats['total'] = pokemons_total_qs['total_pokemons']
		for single_filter in pokemon_filters:
			pokedex_stats['count_' + single_filter] = pokemons_total_qs['count_' + single_filter]


	return {
		"pokemons": pokemons_list,
		"paginator": pokemons_paginator,
		"pokedex_stats": pokedex_stats
	}


def get_pokemon_queryset(qs_annotate, qs_filters, qs_values, qs_order_by):
	pokemons_qs = Pokemon.objects.annotate(
		**qs_annotate
	).filter(
		qs_filters
	).select_related('variant').values(
		*qs_values
	).order_by(qs_order_by)

	return pokemons_qs


def fetch_page(request, page, page_url, **kwargs):

	page_content = {
		"content": "",
		"filters_status": []
	}

	kwargs['search_text'] = request.GET.get("search", "")
	kwargs['settings_filters'] = request.session.get("filters", [])
	kwargs['page'] = page
	kwargs['user'] = request.user
	kwargs['pokemon_language'] = request.session.get("language", "en")
	pokemons_data = fetch_pokemons(**kwargs)

	page_content['filters_status'] = kwargs['settings_filters']
	page_content['pokemon_language'] = kwargs['pokemon_language']

	page_content['pokedex_stats'] = pokemons_data['pokedex_stats']

	print("Archive Queries")
	print(connection.queries)

	page_content['content'] = render_to_string("pokemon/card.html", {
		'pokemons': pokemons_data['pokemons'],
		'is_logged': request.user.is_authenticated
	})

	if page != None:
		pagination_args = {
			'page_url': page_url,
			'paginator': pokemons_data['paginator'],
		}
		if "pokemon_region" in kwargs:
			pagination_args['pokemon_region'] = kwargs['pokemon_region']
		page_content['content'] += render_to_string("pokemon/pagination.html", pagination_args)

	return page_content
