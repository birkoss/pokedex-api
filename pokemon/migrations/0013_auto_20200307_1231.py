# Generated by Django 3.0.3 on 2020-03-07 12:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pokemon', '0012_auto_20200307_0016'),
    ]

    operations = [
        migrations.AddField(
            model_name='userpokemon',
            name='is_gender',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userpokemon',
            name='is_iv',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userpokemon',
            name='is_language',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userpokemon',
            name='is_original_trainer',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userpokemon',
            name='is_pokeball',
            field=models.BooleanField(default=False),
        ),
    ]
