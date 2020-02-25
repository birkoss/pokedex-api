from django.db import models

class Pokemon(models.Model):
	variant = models.ForeignKey('self', blank=True, null=True, on_delete = models.PROTECT, related_name='variants')

	name = models.CharField(max_length=255, default='')

	number = models.CharField(max_length=4, default='')

	def __str__(self):
		return self.name