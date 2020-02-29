from django.db import models

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

	number = models.CharField(max_length=4, default='')

	generation = models.ForeignKey(Generation, blank=True, null=True, on_delete = models.PROTECT, related_name='generations')

	def __str__(self):
		return self.name


