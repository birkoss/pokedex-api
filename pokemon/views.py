from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import connection
from django.db.models import FilteredRelation, Q
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

		pokemon_options = UserPokemon.objects.filter(pokemon=pokemon, user=request.user).first()

		return render(request, "pokemon/options.html", {
			'pokemon': pokemon,
			'options': pokemon_options
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
		"page_url": "pokemon_archive_page"
	})


def pokemon_forms_archive(request):
	return render(request, "pokemon/archive.html", {
		"page_url": "pokemon_forms_archive_page"
	})


def pokemon_pokedex_archive(request, region=None):
	return render(request, "pokemon/archive.html", {
		"page_url": "pokemon_pokedex_archive_page",
		"region": region
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

	return render(request, "pokemon/single.html", {
		'pokemon': pokemons_data['pokemons'][0],
		'variants': variants_data['pokemons']
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

	pokemon_filters = ("is_owned", "is_shiny", "is_pokeball", "is_language", "is_iv", "is_original_trainer", "is_gender")

	pagination = 40

	qs_annotate = {}
	qs_values = ["name", "number", "variant__name", "variant__number"]

	qs_filters = Q()

	order_field = "number"

	# Dynamically add language for name and variant
	for single_language in MODELTRANSLATION_LANGUAGES:
		qs_values.append("name_" + single_language)
		qs_values.append("variant__name_" + single_language)

	if "pokemon_region" in kwargs and kwargs['pokemon_region'] != "":
		qs_filters.add(Q(pokemonregion__region__slug=kwargs['pokemon_region']), Q.AND)
		qs_values.append("pokemonregion__number")
		order_field = "pokemonregion__number"

	if "pokemon_hide" in kwargs:
		for single_filter in kwargs['pokemon_hide']:
			qs_filters.add(Q(**{'t__' + single_filter:False}) | Q(userpokemon__isnull=True), Q.AND)

	if "pokemon_type" in kwargs:
		if kwargs['pokemon_type'] == "pokemons":
			qs_filters.add(Q(variant__isnull=True), Q.AND)
		elif kwargs['pokemon_type'] == "forms":
			qs_filters.add(Q(variant__isnull=False), Q.AND)

	if "pokemon_number" in kwargs:
		qs_filters.add(Q(number=kwargs['pokemon_number']), Q.AND)

	if "variant__number" in kwargs:
		qs_filters.add(Q(variant__number=kwargs['variant__number']), Q.AND)

	if "user" in kwargs:
		if kwargs['user'].is_authenticated:
			for single_filter in pokemon_filters:
				qs_values.append("t__" + single_filter)

			qs_annotate['t'] = FilteredRelation(
				'userpokemon', condition=(Q(userpokemon__user=kwargs['user']) | Q(userpokemon__isnull=True))
			)

	# Get the Pokemons depending on all the differents settings
	pokemons_qs = Pokemon.objects.annotate(
		**qs_annotate
	).filter(
		qs_filters
	).select_related('variant').values(
		*qs_values
	).order_by(order_field)
	# Pagination
	total_pokemons = 0;

	print(kwargs)

	pokemons_paginator = None
	if "page" in kwargs and kwargs['page'] != None:
		paginator = Paginator(pokemons_qs, pagination)
		total_pokemons = paginator.count
		try:
			pokemons_paginator = paginator.page(kwargs['page'])
		except PageNotAnInteger:
			pokemons_paginator = paginator.page(1)
		except EmptyPage:
			pokemons_paginator = paginator.page(paginator.num_pages)
	else:
		pokemons_paginator = pokemons_qs
		total_pokemons = len(pokemons_qs)


	pokemons_list = []
	for single_pokemon in pokemons_paginator:
		pokemon = single_pokemon
		pokemon['visible_number'] = pokemon['number'][:3]

		if 'pokemonregion__number' in single_pokemon and single_pokemon['pokemonregion__number'] != None:
			pokemon['visible_number'] = single_pokemon['pokemonregion__number'][:3]

		if single_pokemon['variant__name'] != None:
			pokemon['name'] = single_pokemon['name'].replace("#NAME#", single_pokemon['variant__name'])

		# Init filters to default values
		for single_filter in pokemon_filters:
			pokemon[ single_filter ] = None

			# Update the filter in they are found in the database
			if "t__" + single_filter in single_pokemon:
				pokemon[ single_filter ] = single_pokemon["t__" + single_filter]

		pokemons_list.append(pokemon)


	return {
		"pokemons": pokemons_list,
		"paginator": pokemons_paginator,
		"total_pokemons": total_pokemons
	}


def fetch_page(request, page, page_url, **kwargs):

	page_content = {
		'content': "",
		'total': 0
	}

	kwargs['hide'] = request.session.get("hide", [])
	kwargs['page'] = page
	kwargs['user'] = request.user

	pokemons_data = fetch_pokemons(**kwargs)

	page_content['total'] = pokemons_data['total_pokemons']

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
