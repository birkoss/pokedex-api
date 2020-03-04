# Generated by Django 3.0.3 on 2020-03-03 11:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pokemon', '0009_auto_20200229_1720'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserPokemon',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_owned', models.BooleanField(default=False)),
                ('is_shiny', models.BooleanField(default=False)),
                ('pokemon', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='pokemon.Pokemon')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]