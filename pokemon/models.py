from django.db import models
from django.contrib.auth.models import User

from birkoss.utils import slugify_model


class Generation(models.Model):
	name = models.CharField(max_length=255, default='')

	def __str__(self):
		return self.name


class Region(models.Model):
	name = models.CharField(max_length=255, default='')

	slug = models.SlugField(max_length=255, blank=True, default='')

	def __str__(self):
		return self.name

	def save(self, *args, **kwargs):
		if not self.slug.strip():
			self.slug = slugify_model(Region, self.__str__())
		super(Region, self).save();


class Pokemon(models.Model):
	variant = models.ForeignKey('self', blank=True, null=True, on_delete = models.PROTECT, related_name='variants')

	name = models.CharField(max_length=255, default='')

	number = models.CharField(max_length=255, default='', blank=True)

	def __str__(self):
		return self.name


class PokemonRegion(models.Model):
	pokemon = models.ForeignKey(Pokemon, blank=True, null=True, on_delete = models.PROTECT)
	region = models.ForeignKey(Region, blank=True, null=True, on_delete = models.PROTECT)

	number = models.CharField(max_length=255, default='')


class UserPokemon(models.Model):
	pokemon = models.ForeignKey(Pokemon, blank=True, null=True, on_delete = models.PROTECT)
	user = models.ForeignKey(User, blank=True, null=True, on_delete = models.PROTECT)

	is_owned = models.BooleanField(default=False)
	is_shiny = models.BooleanField(default=False)
	is_pokeball = models.BooleanField(default=False)
	is_language = models.BooleanField(default=False)
	is_iv = models.BooleanField(default=False)
	is_original_trainer = models.BooleanField(default=False)
	is_gender = models.BooleanField(default=False)