from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404

import urllib.request
import json
import math
from urllib.request import urlopen, Request

from pokemon.models import Pokemon, Generation

def index(request, page=1):
	# @TODO : Logged = datatable, unlogged = pagination
	pagination = 30
	pokemons_list = Pokemon.objects.all()

	paginator = Paginator(pokemons_list, pagination)

	try:
		pokemons = paginator.page(page)
	except PageNotAnInteger:
		pokemons = paginator.page(1)
	except EmptyPage:
		pokemons = paginator.page(paginator.num_pages)

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