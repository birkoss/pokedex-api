from django.contrib import admin

from .models import Pokemon, Generation, Region

admin.site.register(Pokemon)
admin.site.register(Generation)
admin.site.register(Region)