from django.conf.urls import url, include
from django.contrib import admin
from django.urls import path


from pokemon import views as pokemon_views
from base import views as base_views

urlpatterns = [
	path('admin/', admin.site.urls),

	path('', pokemon_views.index, name='pokemon_list'),
	path('<int:page>/', pokemon_views.index, name='pokemon_list_page'),
	
	path('dashboard/', pokemon_views.index, name='user_dashboard'),
	path('dashboard/profile/', base_views.profile, name='user_profile'),

	path('pokemon/<str:pokemon_number>/', pokemon_views.pokemon_detail, name='pokemon_detail'),
	path('import', pokemon_views.import_pokemon, name='import'),
	url(r'^oauth/', include('social_django.urls', namespace='social')),
]
