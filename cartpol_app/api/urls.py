from django.contrib import admin
from django.urls import path
from cartpol_app.api.views.views import StateAV, CountyAV, NeighborhoodAV, ElectoralZoneAV, PoliticalTypeAV, ElectionAV, PoliticalPartyAV, PoliticalAV, VotesAV, ElectionResultsAV, SectionAV, CountysNeighborhoodAV, PoliticalVotesAV, PoliticalPartiesVotesAV
from cartpol_app.api.views.report_view import GenerateReportView

urlpatterns = [
    path('state', StateAV.as_view(), name="state-crud"),
    path('county', CountyAV.as_view(), name="county-crud"),
    path('neighborhood/', NeighborhoodAV.as_view(), name="neighborhood-crud"),
    path('neighborhood/<int:city>', CountysNeighborhoodAV.as_view(), name="neighborhood-crud"),
    path('electoral-zone/', ElectoralZoneAV.as_view(), name="electoral-zone-crud"),
    path('political-type/', PoliticalTypeAV.as_view(), name="political-type-crud"),
    path('election/', ElectionAV.as_view(), name="election-crud"),
    path('political-party/', PoliticalPartyAV.as_view(), name="political-party-crud"),
    path('political/', PoliticalAV.as_view(), name="political-crud"),
    path('votes/', VotesAV.as_view(), name="votes-crud"),
    path('section/', SectionAV.as_view(), name="section-crud"),
    path('political-votes/<int:political_id>', PoliticalVotesAV.as_view(), name="votes-politicals-crud"),
    path('political-party-votes/<int:political_party_id>/<int:city_id>', PoliticalPartiesVotesAV.as_view(), name="votes-parties-crud"),
    path('results/<int:city>/<int:cargo>/<int:year>/', ElectionResultsAV.as_view(), name="election-results"),
    
    path('report/political-votes/<int:cargo>/<int:year>/<int:political_id>', GenerateReportView.as_view(), name="generate-report-politicals-crud"),
]
