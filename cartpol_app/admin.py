from django.contrib import admin
from .models import PoliticalType, PoliticalParty, Election, Political, Votes, State, County, ElectoralZone, Section, Neighborhood

# Register your models here.

admin.site.register([PoliticalType, PoliticalParty, Election, Political, Votes, State, County, ElectoralZone, Section, Neighborhood])