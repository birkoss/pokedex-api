from django.contrib import admin

from .models import Pokemon, Generation, Region, UserPokemon


admin.site.register(Pokemon)
admin.site.register(Generation)
admin.site.register(Region)
admin.site.register(UserPokemon)