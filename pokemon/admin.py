from django.contrib import admin

from .models import Pokemon, Generation, PokemonRegion, Region, UserPokemon


admin.site.register(Pokemon)
admin.site.register(Generation)
admin.site.register(Region)
admin.site.register(PokemonRegion)
admin.site.register(UserPokemon)