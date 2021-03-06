from django.conf.urls import url, include
from django.contrib import admin
from django.urls import path

from pokemon import views as pokemon_views
from base import views as base_views


handler404 = 'base.views.error_404'


urlpatterns = [
	path('admin/', admin.site.urls),

	path('pokemons/<int:page>', pokemon_views.pokemons_page, name='pokemons_page'),

	# Archive Pokemon
	path('', pokemon_views.pokemon_archive, name='pokemon_archive'),

	path('forms', pokemon_views.pokemon_forms_archive, name='pokemon_forms_archive'),

	path('pokedex/<str:region>', pokemon_views.pokemon_pokedex_archive, name='pokemon_pokedex_archive'),

	# Single Pokemon page
	path('pokemon/<str:pokemon_number>/', pokemon_views.pokemon_single, name='pokemon_single'),

	# Single Pokemon Options (for the modal) 
	path('pokemon/<str:pokemon_number>/options', pokemon_views.pokemon_options, name='pokemon_single_options'),
	
	path('bulk-edit', pokemon_views.bulk_edit, name='bulk_edit'),

	path('settings', base_views.user_settings, name='user_settings'),
	path('logout', base_views.user_logout, name='logout'),
	path('profile', base_views.user_profile, name='user_profile'),
	
	path('contact', base_views.contact, name='contact'),

	path('import', pokemon_views.import_pokemon, name='import'),
	
	url(r'^oauth/', include('social_django.urls', namespace='social')),
]
