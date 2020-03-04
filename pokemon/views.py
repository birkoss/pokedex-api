from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import FilteredRelation, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404

import urllib.request
import json
import math
from urllib.request import urlopen, Request

from pokemon.models import Pokemon, Generation, UserPokemon


def pokemon_toggle(request, pokemon_number):
	response = {
		"status": "pending"
	}

	option_name = request.POST.get("option", "")
	if option_name == "":
		response['status'] = "error"
		response['msg'] = "You must specific an option!"
		return JsonResponse(response)

	if not request.user.is_authenticated:
		response['status'] = "error"
		response['msg'] = "You must be logged in!"
		return JsonResponse(response)

	pokemon = Pokemon.objects.filter(number=pokemon_number).first()
	if pokemon is None:
		response['status'] = "error"
		response['msg'] = "This pokemon doesn't exist!"
		return JsonResponse(response)

	user_pokemon = UserPokemon.objects.filter(pokemon=pokemon, user=request.user).first()
	if user_pokemon is None:
		user_pokemon = UserPokemon(pokemon=pokemon, user=request.user)
		user_pokemon.save()

	try:
		setattr(user_pokemon, "is_" + option_name, not getattr(user_pokemon, "is_" + option_name))
	except AttributeError:
		response['status'] = "error"
		response['msg'] = "This option doesn't exist!"
		return JsonResponse(response)

	user_pokemon.save();

	response['status'] = "ok"

	return JsonResponse(response)


def test(request):
	pokemons_qs = Pokemon.objects.annotate(
		t=FilteredRelation(
			'userpokemon', condition=(Q(userpokemon__user=request.user) | Q(userpokemon__isnull=True))
		)
	).filter(
		
	).values(
		"name", "number", "t__is_owned", "t__is_shiny"
	)

	print(pokemons_qs.query)

#	pokemons_qs = Pokemon.objects.filter(
#		Q(userpokemon__user=request.user) | Q(userpokemon__isnull=True)
#	).values(
#		"name", "number", "userpokemon__is_owned", "userpokemon__is_shiny"
#	)
	page = 1

	paginator = Paginator(pokemons_qs, 5)
	try:
		pokemons_list = paginator.page(page)
	except PageNotAnInteger:
		pokemons_list = paginator.page(1)
	except EmptyPage:
		pokemons_list = paginator.page(paginator.num_pages)

	pokemons = []
	for single_pokemon in pokemons_list:
		pokemons.append({
			'name': single_pokemon['name'],
			'is_owned': single_pokemon['t__is_owned'],
			'is_shiny': single_pokemon['t__is_shiny'],
		})

	return render(request, "pokemon/test.html", {
		'pokemons': pokemons
	})


def index(request, page=1):
	# @TODO : Logged = datatable, unlogged = pagination
	pagination = 30

	pokemons_qs = Pokemon.objects.annotate(
		t=FilteredRelation(
			'userpokemon', condition=(Q(userpokemon__user=request.user) | Q(userpokemon__isnull=True))
		)
	).filter(
		
	).values(
		"name", "number", "t__is_owned", "t__is_shiny"
	)

	print("Query:")
	print(pokemons_qs.query)

	paginator = Paginator(pokemons_qs, pagination)

	try:
		pokemons_list = paginator.page(page)
	except PageNotAnInteger:
		pokemons_list = paginator.page(1)
	except EmptyPage:
		pokemons_list = paginator.page(paginator.num_pages)

	pokemons = []
	for single_pokemon in pokemons_qs:
		pokemons.append({
			'name': single_pokemon['name'],
			'number': single_pokemon['number'],
			'is_owned': single_pokemon['t__is_owned'],
			'is_shiny': single_pokemon['t__is_shiny'],
		})

	return render(request, "pokemon/index.html", {
		'pokemons': pokemons,
		'mode': 'list'
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