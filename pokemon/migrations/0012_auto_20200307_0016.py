# Generated by Django 3.0.3 on 2020-03-07 00:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pokemon', '0011_auto_20200306_1916'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pokemon',
            name='number',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
    ]
