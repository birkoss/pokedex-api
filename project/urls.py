from django.conf.urls import url, include
from django.contrib import admin
from django.urls import path

from pokemon import views as pokemon_views
from base import views as base_views


handler404 = 'base.views.error_404'


urlpatterns = [
	path('admin/', admin.site.urls),

	# Archive Pokemon
	path('', pokemon_views.index, name='pokemon_archive'),
	path('forms', pokemon_views.pokemons_forms_archive, name='pokemon_form_archive'),

	path('page/<int:page>', pokemon_views.pokemons_cards, name='pokemon_archive_page'),

	# Single Pokemon page
	path('pokemon/<str:pokemon_number>/', pokemon_views.pokemon_single, name='pokemon_single'),

	# Single Pokemon Options (for the modal) 
	path('pokemon/<str:pokemon_number>/options', pokemon_views.pokemon_options, name='pokemon_single_options'),
	
	path('logout', base_views.user_logout, name='logout'),
	path('profile', base_views.user_profile, name='user_profile'),

	path('import', pokemon_views.import_pokemon, name='import'),
	
	url(r'^oauth/', include('social_django.urls', namespace='social')),
]
