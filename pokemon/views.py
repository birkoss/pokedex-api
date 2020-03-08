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

from pokemon.models import Pokemon, Generation, UserPokemon

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
		"type": "pokemons"
	})


def pokemon_forms_archive(request):
	return render(request, "pokemon/archive.html", {
		"type": "forms"
	})


def pokemon_pokedex_archive(request, region):
	return render(request, "pokemon/archive.html", {
		"type": "pokemons",
		"region": region
	})


def pokemon_archive_page(request, page=1):
	request_header_requested_with = request.META.get("HTTP_X_REQUESTED_WITH", "")

	if request_header_requested_with != "XMLHttpRequest":
		return redirect('pokemon_archive')

	pokemon_type = request.GET.get("type", "pokemons")
	if pokemon_type == "forms":
		page = None

	pokemon_region = request.GET.get("region", "")

	hide = request.session.get("hide", [])

	pokemons_data = pokemons_list = fetch_pokemons(pokemon_region=pokemon_region, pokemon_type=pokemon_type, user=request.user, page=page, pokemon_hide=hide)

	print("Archive Queries")
	print(connection.queries)

	content = render_to_string("pokemon/card.html", {
		'pokemons': pokemons_data['pokemons'],
		'is_logged': request.user.is_authenticated
	})

	if page != None:
		content += render_to_string("pokemon/pagination.html", {
		'paginator': pokemons_data['paginator'],
	})

	return HttpResponse(content)


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

	# Import Pokemons from their names
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
				pokemon = Pokemon(**data)
				pokemon.save();
				print("Created Form: " + single_pokemon['number'])


	return HttpResponse("<p>test2</p>")


def fetch_pokemons(**kwargs):

	pokemon_filters = ("is_owned", "is_shiny", "is_pokeball", "is_language", "is_iv", "is_original_trainer", "is_gender")

	pagination = 40

	qs_annotate = {}
	qs_values = ["name", "number", "variant__name", "variant__number"]

	qs_filters = Q()

	# Dynamically add language for name and variant
	for single_language in MODELTRANSLATION_LANGUAGES:
		qs_values.append("name_" + single_language)
		qs_values.append("variant__name_" + single_language)

	if "pokemon_region" in kwargs and kwargs['pokemon_region'] != "":
		qs_filters.add(Q(pokemonregion__region__slug=kwargs['pokemon_region']), Q.AND)
		qs_values.append("pokemonregion__number")

	if "pokemon_hide" in kwargs:
		for single_filter in kwargs['pokemon_hide']:
			qs_filters.add(Q(**{'t__' + single_filter:False}) | Q(userpokemon__isnull=True), Q.AND)

	if "pokemon_type" in kwargs:
		if kwargs['pokemon_type'] == "pokemons":
			qs_filters.add(Q(variant__isnull=True), Q.AND)
		elif kwargs['pokemon_type'] == "forms":
			pagination = 1000
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
	).order_by('number')

	# Pagination
	pokemons_paginator = None
	if "page" in kwargs and kwargs['page'] != None:
		paginator = Paginator(pokemons_qs, pagination)
		try:
			pokemons_paginator = paginator.page(kwargs['page'])
		except PageNotAnInteger:
			pokemons_paginator = paginator.page(1)
		except EmptyPage:
			pokemons_paginator = paginator.page(paginator.num_pages)
	else:
		pokemons_paginator = pokemons_qs


	pokemons_list = []
	for single_pokemon in pokemons_paginator:
		pokemon = single_pokemon
		pokemon['visible_number'] = pokemon['number'][:3]

		if 'pokemonregion__number' in single_pokemon and single_pokemon['pokemonregion__number'] != None:
			pokemon['visible_number'] = single_pokemon['pokemonregion__number'][:3]

		if single_pokemon['variant__name'] != None:
			pokemon['name'] = single_pokemon['variant__name'] + " " + pokemon['name']

		# Init filters to default values
		for single_filter in pokemon_filters:
			pokemon[ single_filter ] = None

			# Update the filter in they are found in the database
			if "t__" + single_filter in single_pokemon:
				pokemon[ single_filter ] = single_pokemon["t__" + single_filter]

		pokemons_list.append(pokemon)


	return {
		"pokemons": pokemons_list,
		"paginator": pokemons_paginator
	}

