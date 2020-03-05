from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import connection
from django.db.models import FilteredRelation, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404

import urllib.request
import json
import math
from urllib.request import urlopen, Request

from pokemon.models import Pokemon, Generation, UserPokemon


@login_required
def pokemon_options(request, pokemon_number):
	if request.method == "GET":
		pokemon = Pokemon.objects.filter(number=pokemon_number).first()

		pokemon_options = UserPokemon.objects.filter(pokemon=pokemon, user=request.user).first()

		print(pokemon_options)

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


def index(request, page=1):
	# @TODO : Logged = datatable, unlogged = pagination
	pagination = 30

	if request.user.is_authenticated:
		pokemons_list = Pokemon.objects.annotate(
			t=FilteredRelation(
				'userpokemon', condition=(Q(userpokemon__user=request.user) | Q(userpokemon__isnull=True))
			)
		).filter(
			
		).values(
			"name", "number", "t__is_owned", "t__is_shiny"
		)
	else:
		pokemons_qs = Pokemon.objects.all().values(
			"name", "number"
		)

		paginator = Paginator(pokemons_qs, pagination)

		try:
			pokemons_list = paginator.page(page)
		except PageNotAnInteger:
			pokemons_list = paginator.page(1)
		except EmptyPage:
			pokemons_list = paginator.page(paginator.num_pages)

	pokemons = []
	for single_pokemon in pokemons_list:
		pokemon = {
			'name': single_pokemon['name'],
			'number': single_pokemon['number'],
			'is_owned': None,
			'is_shiny': None,

		}

		if request.user.is_authenticated:
			pokemon['is_owned'] = single_pokemon['t__is_owned']
			pokemon['is_shiny'] = single_pokemon['t__is_shiny']
		
		pokemons.append(pokemon)

	return render(request, "pokemon/index.html", {
		'pokemons': pokemons,
		'mode': 'list',
		'paginator': pokemons_list
	})


def pokemon_detail(request, pokemon_number=None):
	pokemon = get_object_or_404(Pokemon, number=pokemon_number)

	return render(request, "pokemon/detail.html", {'pokemon': pokemon})


def import_pokemon(request):
	headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'}

	reg_url = "https://birkoss.com/pokemon.json"
	req = Request(url=reg_url, headers=headers)

	with urllib.request.urlopen(req) as url:
		data = json.loads(url.read().decode())
		for single_pokemon in data['pokemons']:
			pokemon = Pokemon.objects.filter(name_en=single_pokemon['names/en'])
			if len(pokemon) == 0:
				data = {}
				data['number'] = single_pokemon['national']
				for mlid in ('names/en', 'names/fr', 'names/jp', 'names/de', 'names/kr'):
					if mlid in single_pokemon:
						data[mlid.replace("s/", "_")] = single_pokemon[mlid]

				data['generation'] = Generation.objects.filter(name=single_pokemon['generation'])[0]

				# Create the new Pokemon
				pokemon = Pokemon(**data)
				pokemon.save()

	return HttpResponse("<p>test2</p>")