from django.urls import path

from cartpol_app.api.views.report_view import GenerateReportView
from cartpol_app.api.views.views import (CountyAV, CountysNeighborhoodAV,
                                         ElectionAV, ElectionResultsAV,
                                         ElectoralZoneAV, NeighborhoodAV,
                                         PoliticalAV, PoliticalPartiesVotesAV,
                                         PoliticalPartyAV, PoliticalTypeAV,
                                         PoliticalVotesAV, SectionAV, StateAV,
                                         VotesAV)

urlpatterns = [
    path('state', StateAV.as_view(), name="state-crud"),
    path('county', CountyAV.as_view(), name="county-crud"),
    path('neighborhood/', NeighborhoodAV.as_view(), name="neighborhood-cr"),
    path('neighborhood/<int:neighborhood_id>',
         NeighborhoodAV.as_view(), name="neighborhood-ud"),

    path('neighborhood/city/<int:city>',
         CountysNeighborhoodAV.as_view(), name="neighborhood-crud"),
    path('electoral-zone/', ElectoralZoneAV.as_view(), name="electoral-zone-crud"),
    path('political-type/', PoliticalTypeAV.as_view(), name="political-type-crud"),
    path('election/', ElectionAV.as_view(), name="election-crud"),
    path('political-party/', PoliticalPartyAV.as_view(),
         name="political-party-crud"),
    path('political-party/<int:year>', PoliticalPartyAV.as_view(),
         name="political-party-crud"),
    path('political/',
         PoliticalAV.as_view(), name="political-crud"),
    path('votes/', VotesAV.as_view(), name="votes-crud"),
    path('section/<int:section_id>', SectionAV.as_view(), name="section-crud"),
    path('section/', SectionAV.as_view(), name="section-crud"),
    path('political-votes/<int:political_id>',
         PoliticalVotesAV.as_view(), name="votes-politicals-crud"),
    path('political-party-votes/<int:political_party_id>/<int:city_id>',
         PoliticalPartiesVotesAV.as_view(), name="votes-parties-crud"),
    path('results/<int:city>/<int:cargo>/<int:year>/',
         ElectionResultsAV.as_view(), name="election-results"),

    path('report/political-votes/<int:year>/<int:political_id>',
         GenerateReportView.as_view(), name="generate-report-politicals-crud"),
]
