from django.contrib import admin
from django.urls import path
from cartpol_app.api.views import StateAV, CountyAV, NeighborhoodAV, ElectoralZoneAV, PoliticalTypeAV, ElectionAV, PoliticalPartyAV, PoliticalAV, VotesAV, ElectionResultsAV, SectionAV

urlpatterns = [
    path('state/', StateAV.as_view(), name="state-crud"),
    path('county/', CountyAV.as_view(), name="county-crud"),
    path('neighborhood/', NeighborhoodAV.as_view(), name="neighborhood-crud"),
    path('electoral-zone/', ElectoralZoneAV.as_view(), name="electoral-zone-crud"),
    path('political-type/', PoliticalTypeAV.as_view(), name="political-type-crud"),
    path('election/', ElectionAV.as_view(), name="election-crud"),
    path('political-party/', PoliticalPartyAV.as_view(), name="political-party-crud"),
    path('political/', PoliticalAV.as_view(), name="political-crud"),
    path('votes/', VotesAV.as_view(), name="votes-crud"),
    path('section/', SectionAV.as_view(), name="section-crud"),
    path('results/<int:city>/<int:cargo>/<int:year>/', ElectionResultsAV.as_view(), name="election-results")
]
