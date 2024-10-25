# Generated by Django 4.2.5 on 2023-10-25 00:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="County",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=40)),
            ],
        ),
        migrations.CreateModel(
            name="Election",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("year", models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name="ElectoralZone",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("identifier", models.CharField(max_length=40)),
                ("cep", models.CharField(default="", max_length=10)),
                ("address", models.CharField(default="", max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name="Political",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("full_name", models.CharField(max_length=200)),
                (
                    "election",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="cartpol_app.election",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="PoliticalParty",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=40)),
                ("full_name", models.CharField(max_length=200)),
                ("active", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="PoliticalType",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=40)),
                ("description", models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name="State",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=8)),
                ("full_name", models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name="Votes",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("quantity", models.IntegerField()),
                ("description", models.CharField(max_length=200)),
                (
                    "political",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="cartpol_app.political",
                    ),
                ),
                (
                    "zone",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="cartpol_app.electoralzone",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="political",
            name="political_party",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="cartpol_app.politicalparty",
            ),
        ),
        migrations.AddField(
            model_name="political",
            name="political_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="cartpol_app.politicaltype",
            ),
        ),
        migrations.CreateModel(
            name="Neighborhood",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=40)),
                (
                    "county",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="cartpol_app.county",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="electoralzone",
            name="neighborhood",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="cartpol_app.neighborhood",
            ),
        ),
        migrations.AddField(
            model_name="county",
            name="state",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="cartpol_app.state"
            ),
        ),
    ]
