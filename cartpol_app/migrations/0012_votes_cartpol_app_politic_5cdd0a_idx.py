# Generated by Django 5.0.6 on 2024-11-13 15:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cartpol_app', '0011_remove_section_map_neighborhood_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='votes',
            index=models.Index(fields=['political'], name='cartpol_app_politic_5cdd0a_idx'),
        ),
    ]