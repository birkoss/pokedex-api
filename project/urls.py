from django.conf.urls import url, include
from django.contrib import admin
from django.urls import path

from pokemon import views as pokemon_views
from base import views as base_views

urlpatterns = [
	path('admin/', admin.site.urls),

	path('', pokemon_views.index, name='pokemon_list'),
	
	path('logout/', base_views.user_logout, name='logout'),
	path('dashboard/', pokemon_views.index, name='user_dashboard'),
	path('dashboard/profile/', base_views.user_profile, name='user_profile'),

	path('pokemons/cards/<int:page>', pokemon_views.pokemons_cards, name='pokemons_cards'),
	path('pokemons/options', pokemon_views.pokemons_options, name='pokemons_options'),
	
	path('pokemon/<str:pokemon_number>/options', pokemon_views.pokemon_options, name='pokemon_options'),
	path('pokemon/<str:pokemon_number>/', pokemon_views.pokemon_detail, name='pokemon_detail'),
	
	path('import', pokemon_views.import_pokemon, name='import'),
	
	url(r'^oauth/', include('social_django.urls', namespace='social')),
]
