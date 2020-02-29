from django.contrib import admin
from django.urls import path

from pokemon import views as pokemon_views
from base import views as base_views

urlpatterns = [
	path('admin/', admin.site.urls),

	path('', pokemon_views.index, name='index'),
	path('login/', base_views.login, name='login'),
	path('register/', base_views.register, name='register'),
	path('forgot-password/', base_views.forgot_password, name='forgot_password'),
	path('pokemon/<str:pokemon_number>/', pokemon_views.pokemon_detail, name='pokemon_detail'),
	path('import', pokemon_views.import_pokemon, name='import'),
]
