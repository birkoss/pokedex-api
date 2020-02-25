from django.contrib import admin
from django.urls import path

from pokemon import views as pokemon_views

urlpatterns = [
	path('admin/', admin.site.urls),

	path('', pokemon_views.index, name='index'),
]
