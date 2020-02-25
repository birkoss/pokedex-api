from django.shortcuts import render

from pokemon.models import Pokemon

def index(request):
	pokemons = Pokemon.objects.all()

	return render(request, "pokemon/index.html", {'pokemons': pokemons})