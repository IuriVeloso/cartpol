from django.db.models import OuterRef, Q, Subquery, Sum
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from cartpol_app.api.serializers import (CountySerializer, ElectionSerializer,
                                         ElectoralZoneSerializer,
                                         NeighborhoodSerializer,
                                         PoliticalPartySerializer,
                                         PoliticalSerializer,
                                         PoliticalTypeSerializer,
                                         SectionSerializer, StateSerializer,
                                         VotesSerializer)
from cartpol_app.models import (County, Election, ElectoralZone, Neighborhood,
                                Political, PoliticalParty, PoliticalType,
                                Section, State, Votes)


class StateAV(APIView):
    def get(self, request):
        states = State.objects.all().order_by('name')
        should_search_state = request.query_params.get('name', False)
        if should_search_state:
            states = states.filter(name=should_search_state)
        state_serializer = StateSerializer(states, many=True)
        return Response(state_serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        state_serializer = StateSerializer(data=request.data)
        if state_serializer.is_valid():
            state_serializer.save()
            return Response(state_serializer.data, status=status.HTTP_201_CREATED)
        return Response(state_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CountyAV(APIView):
    def get(self, request):
        counties = County.objects.all().order_by('name')
        should_search_county = request.query_params.get('name', False)
        should_search_state = request.query_params.get('state', False)
        should_search_state_id = request.query_params.get('state_id', False)
        should_search_tse_id = request.query_params.get('tse_id', False)
        if should_search_state:
            counties = counties.filter(state__name=should_search_state)
        if should_search_state_id:
            counties = counties.filter(state__id=should_search_state_id)
        if should_search_county:
            counties = counties.filter(name=should_search_county)
        if should_search_tse_id:
            counties = counties.filter(tse_id=should_search_tse_id)

        county_serializer = CountySerializer(
            counties, many=True)
        return Response(county_serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        county_serializer = CountySerializer(data=request.data)
        if county_serializer.is_valid():
            county_serializer.save()
            return Response(county_serializer.data, status=status.HTTP_201_CREATED)
        return Response(county_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NeighborhoodAV(APIView):
    def get(self, request):
        neighborhoods = Neighborhood.objects.all()
        should_search_neighborhood = request.query_params.get('name', False)
        should_search_county = request.query_params.get('county', False)
        should_search_county_tse_id = request.query_params.get(
            'county_tse_id', False)

        if should_search_neighborhood:
            neighborhoods = neighborhoods.filter(
                name__unaccent=should_search_neighborhood)
        if should_search_county:
            neighborhoods = neighborhoods.filter(
                county__name=should_search_county)
        if should_search_county_tse_id:
            neighborhoods = neighborhoods.filter(
                county__tse_id=should_search_county_tse_id)

        neighborhood_serializer = NeighborhoodSerializer(
            neighborhoods, many=True)
        return Response(neighborhood_serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        neighborhood_serializer = NeighborhoodSerializer(
            data=request.data, many=isinstance(request.data, list))
        if neighborhood_serializer.is_valid():
            neighborhood_serializer.save()
            return Response(neighborhood_serializer.data, status=status.HTTP_201_CREATED)
        return Response(neighborhood_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, neighborhood_id=None):
        section = get_object_or_404(Neighborhood, pk=neighborhood_id)
        section_data = JSONParser().parse(request)
        section_serializer = NeighborhoodSerializer(section)

        section_serializer.update(
            instance=section, validated_data=section_data)

        return Response(section_serializer.data, status=status.HTTP_200_OK)


class CountysNeighborhoodAV(APIView):
    def get(self, request, city):
        neighborhoods = Neighborhood.objects.all().filter(county_id=int(city))
        neighborhood_serializer = NeighborhoodSerializer(
            neighborhoods, many=True)
        return Response(neighborhood_serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        neighborhood_serializer = NeighborhoodSerializer(data=request.data)
        if neighborhood_serializer.is_valid():
            neighborhood_serializer.save()
            return Response(neighborhood_serializer.data, status=status.HTTP_201_CREATED)
        return Response(neighborhood_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ElectoralZoneAV(APIView):
    def get(self, request):
        electoral_zones = ElectoralZone.objects.all()
        should_search_electoral_zone = request.query_params.get(
            'identifier', False)
        should_search_year = request.query_params.get(
            'year', False)
        should_search_county = request.query_params.get('county', False)
        should_search_county_tse_id = request.query_params.get(
            'county_tse_id', False)

        if should_search_electoral_zone:
            electoral_zones = electoral_zones.filter(
                identifier=should_search_electoral_zone)
        if should_search_county:
            electoral_zones = electoral_zones.filter(
                county__name=should_search_county)
        if should_search_county_tse_id:
            electoral_zones = electoral_zones.filter(
                county__tse_id=should_search_county_tse_id)
        if should_search_year:
            electoral_zones = electoral_zones.filter(
                year=should_search_year)

        electoral_zone_serializer = ElectoralZoneSerializer(
            electoral_zones, many=True)
        return Response(electoral_zone_serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        electoral_zone_serializer = ElectoralZoneSerializer(data=request.data)
        if electoral_zone_serializer.is_valid():
            electoral_zone_serializer.save()
            return Response(electoral_zone_serializer.data, status=status.HTTP_201_CREATED)
        return Response(electoral_zone_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PoliticalTypeAV(APIView):
    def get(self, request):
        political_types = PoliticalType.objects.all().order_by('name')

        should_search_election = request.query_params.get(
            'election', False)
        if should_search_election:
            political_types = political_types.filter(
                election=should_search_election)

        political_type_serializer = PoliticalTypeSerializer(
            political_types, many=True)
        return Response(political_type_serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        political_type_serializer = PoliticalTypeSerializer(data=request.data)
        if political_type_serializer.is_valid():
            political_type_serializer.save()
            return Response(political_type_serializer.data, status=status.HTTP_201_CREATED)
        return Response(political_type_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PoliticalPartyAV(APIView):
    def get(self, request):
        political_parties = PoliticalParty.objects.all()

        should_search_party = request.query_params.get('name', False)
        if should_search_party:
            political_parties = political_parties.filter(
                name=should_search_party)

        political_party_serializer = PoliticalPartySerializer(
            political_parties, many=True)
        return Response(political_party_serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        political_party_serializer = PoliticalPartySerializer(
            data=request.data)
        if political_party_serializer.is_valid():
            political_party_serializer.save()
            return Response(political_party_serializer.data, status=status.HTTP_201_CREATED)
        return Response(political_party_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ElectionAV(APIView):
    def get(self, request):
        elections = Election.objects.all().order_by('year')
        election_serializer = ElectionSerializer(elections, many=True)
        return Response(election_serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        election_serializer = ElectionSerializer(data=request.data)
        if election_serializer.is_valid():
            election_serializer.save()
            return Response(election_serializer.data, status=status.HTTP_201_CREATED)
        return Response(election_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PoliticalAV(APIView):
    def get(self, request):
        politicals = Political.objects.all().order_by('name')

        should_search_political_code = request.query_params.get(
            'political_code', False)
        should_search_full_name = request.query_params.get('full_name', False)
        should_search_county_id = request.query_params.get('county_id', False)
        should_search_state_id = request.query_params.get('state_id', False)
        should_search_year = request.query_params.get('year', False)
        should_search_political_type = request.query_params.get(
            'political_type_id', False)
        if should_search_full_name:
            politicals = politicals.filter(full_name=should_search_full_name)
        if should_search_political_code:
            politicals = politicals.filter(
                political_code=should_search_political_code)
        if should_search_county_id:
            county = get_object_or_404(County, pk=should_search_county_id)
            politicals = politicals.filter(
                Q(region_id=int(county.id))
                | Q(region='federal')
                | (Q(region='state') & Q(region_id=county.state_id)))
        if should_search_state_id:
            politicals = politicals.filter(
                (Q(region='federal')
                 | (Q(region='state')
                    & Q(region_id=should_search_state_id)))
            )
        if should_search_year:
            politicals = politicals.filter(
                election__year=int(should_search_year))
        if should_search_political_type:
            politicals = politicals.filter(
                political_type=int(should_search_political_type))

        political_serializer = PoliticalSerializer(politicals, many=True)
        return Response(political_serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        political_serializer = PoliticalSerializer(
            data=request.data, many=isinstance(request.data, list))
        if political_serializer.is_valid():
            political_serializer.save()
            return Response(political_serializer.data, status=status.HTTP_201_CREATED)
        return Response(political_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VotesAV(APIView):
    def get(self, request):
        votes = Votes.objects.filter(section__neighborhood=28)
        votes_serializer = VotesSerializer(votes, many=True)
        return Response(votes_serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        votes_serializer = VotesSerializer(
            data=request.data, many=isinstance(request.data, list))
        if votes_serializer.is_valid():
            votes_serializer.save()
            return Response(votes_serializer.data, status=status.HTTP_201_CREATED)
        return Response(votes_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SectionAV(APIView):
    def get(self, request, section_id=None):
        sections = Section.objects.all()

        if bool(section_id):
            sections = sections.filter(pk=section_id)

        should_search_county = request.query_params.get('county', False)
        should_search_county_tse_id = request.query_params.get(
            'county_tse_id', False)
        should_search_electoral_zone = request.query_params.get(
            'electoral_zone', False)
        should_search_identifier = request.query_params.get(
            'identifier', False)
        should_search_year = request.query_params.get(
            'year', False)
        if should_search_county:
            sections = sections.filter(
                neighborhood__county__name=should_search_county)
        if should_search_electoral_zone:
            sections = sections.filter(
                electoral_zone__identifier=should_search_electoral_zone)
        if should_search_identifier:
            sections = sections.filter(identifier=should_search_identifier)
        if should_search_county_tse_id:
            sections = sections.filter(
                neighborhood__county__tse_id=should_search_county_tse_id)
        if should_search_year:
            sections = sections.filter(
                electoral_zone__year=should_search_year)

        section_serializer = SectionSerializer(sections, many=True)
        return Response(section_serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        section_serializer = SectionSerializer(
            data=request.data, many=isinstance(request.data, list))
        if section_serializer.is_valid():
            section_serializer.save()
            return Response(section_serializer.data, status=status.HTTP_201_CREATED)
        return Response(section_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, section_id=None):
        section = get_object_or_404(Section, pk=section_id)
        section_data = JSONParser().parse(request)
        section_serializer = SectionSerializer(section, data=section_data)
        if section_serializer.is_valid():
            section_serializer.save()
            return Response(section_serializer.data, status=status.HTTP_200_OK)
        return Response(section_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PoliticalVotesAV(APIView):
    def get(self, request, political_id):
        political = get_object_or_404(Political, pk=political_id)

        votes_queryset = Votes.objects.filter(political_id=int(political_id))

        should_search_county_id = request.query_params.get('county_id', False)

        region_id = political.region_id

        if should_search_county_id:
            votes_queryset = votes_queryset.filter(
                section__neighborhood__county=should_search_county_id)
            region_id = should_search_county_id

        total_candidate_votes = votes_queryset \
            .values('section__neighborhood__map_neighborhood')\
            .annotate(total_votes=Sum('quantity'))

        total_votes = votes_queryset.aggregate(total=Sum('quantity'))['total']

        political_filter = Political.objects.filter(
            political_type=political.political_type,
            election=political.election
        ).values('id')

        neighborhood_filter = Neighborhood.objects.filter(
            county=region_id
        ).values('id')

        total_neighborhoods_votes = Votes.objects \
            .filter(
                political_id__in=Subquery(political_filter),
                section__neighborhood_id__in=Subquery(neighborhood_filter)
            ) \
            .values('section__neighborhood__map_neighborhood') \
            .annotate(total=Sum('quantity'))

        total_neighborhoods_votes_dict = {
            item['section__neighborhood__map_neighborhood']: item['total'] for item in total_neighborhoods_votes}

        total_place_votes = sum(total_neighborhoods_votes_dict.values())

        votes_by_neighborhood = []

        min_ruesp_can, max_ruesp_can = 1.0, 0.0
        min_rcan_uesp, max_rcan_uesp = 1.0, 0.0

        for vote in total_candidate_votes:
            total_value = vote['total_votes']
            neighborhood_name = vote['section__neighborhood__map_neighborhood']
            total_neighborhood_votes = total_neighborhoods_votes_dict[neighborhood_name]

            ruesp_can = round(total_value / total_votes, 6)
            rcan_uesp = round(total_value / total_neighborhood_votes, 6)
            ruesp = round(total_neighborhood_votes / total_place_votes, 6)

            min_ruesp_can, max_ruesp_can = min(
                min_ruesp_can, ruesp_can), max(max_ruesp_can, ruesp_can)
            min_rcan_uesp, max_rcan_uesp = min(
                min_rcan_uesp, rcan_uesp), max(max_rcan_uesp, rcan_uesp)

            votes_by_neighborhood.append({
                'total_votes': total_value,
                'neighborhood': neighborhood_name,
                'ruesp_can': ruesp_can,
                'rcan_uesp': rcan_uesp,
                'ruesp': ruesp
            })

        return Response({
            "min_ruesp_can": min_ruesp_can,
            "max_ruesp_can": max_ruesp_can,
            "min_rcan_uesp": min_rcan_uesp,
            "max_rcan_uesp": max_rcan_uesp,
            "total_political_votes": total_votes,
            "votes": votes_by_neighborhood
        }, status=status.HTTP_200_OK)


class PoliticalStateVotesAV(APIView):
    def get(self, request, political_id):
        political = get_object_or_404(Political, pk=political_id)

        should_search_state_id = request.query_params.get('state_id', False)

        region_id = should_search_state_id

        if not should_search_state_id:
            raise Exception("state_id is required")
        
        votes_queryset = Votes.objects.filter(political_id=int(political_id),
                                              section__neighborhood__county__state=region_id)


        county_filter = County.objects.filter(
            state=region_id
        ).values('id')
        political_filter = Political.objects.filter(
            political_type=political.political_type,
            election=political.election
        ).values('id')
        
        total_candidate_votes_queryset = votes_queryset \
            .values('section__neighborhood__county__name')\
            .annotate(total_votes=Sum('quantity'))

        total_votes = votes_queryset.aggregate(total=Sum('quantity'))['total']

        total_state_votes_queryset = Votes.objects \
            .filter(
                section__neighborhood__county_id__in=Subquery(county_filter),
                political_id__in=Subquery(political_filter),
            ) \
            .values('section__neighborhood__county__name') \
            .annotate(total=Sum('quantity'))

        total_state_votes_dict = {
            item['section__neighborhood__county__name']: item['total'] for item in total_state_votes_queryset}

        total_place_votes = sum(total_state_votes_dict.values())

        votes_by_state = []

        min_ruesp_can, max_ruesp_can = 1.0, 0.0
        min_rcan_uesp, max_rcan_uesp = 1.0, 0.0

        for vote in total_candidate_votes_queryset:
            total_value = vote['total_votes']
            county_name = vote['section__neighborhood__county__name']
            total_state_votes = total_state_votes_dict[county_name]

            ruesp_can = round(total_value / total_votes, 6)
            rcan_uesp = round(total_value / total_state_votes, 6)
            ruesp = round(total_state_votes / total_place_votes, 6)

            min_ruesp_can, max_ruesp_can = min(
                min_ruesp_can, ruesp_can), max(max_ruesp_can, ruesp_can)
            min_rcan_uesp, max_rcan_uesp = min(
                min_rcan_uesp, rcan_uesp), max(max_rcan_uesp, rcan_uesp)

            votes_by_state.append({
                'total_votes': total_value,
                'county': county_name,
                'ruesp_can': ruesp_can,
                'rcan_uesp': rcan_uesp,
                'ruesp': ruesp
            })

        return Response({
            "min_ruesp_can": min_ruesp_can,
            "max_ruesp_can": max_ruesp_can,
            "min_rcan_uesp": min_rcan_uesp,
            "max_rcan_uesp": max_rcan_uesp,
            "total_political_votes": total_votes,
            "votes": votes_by_state
        }, status=status.HTTP_200_OK)


class PoliticalPartiesVotesAV(APIView):
    def get(self, request, political_party_id, city_id):
        total_political_party_votes = Votes.objects\
            .filter(political__political_party__id=int(political_party_id),
                    political__region_id=int(city_id))\
            .values('section__neighborhood', 'section__neighborhood__name')\
            .annotate(total_votes=Sum('quantity'))

        total_votes = Votes.objects.filter(political__political_party__id=int(political_party_id),
                                           political__region_id=int(city_id))\
            .aggregate(Sum('quantity'))
        total_neighborhoods_votes = Votes.objects.values(
            'section__neighborhood').annotate(total=Sum('quantity'))

        votes_by_neighborhood = []

        total_political_parties_votes = total_votes.get("quantity__sum")

        for vote in total_political_party_votes:
            total_value = vote['total_votes']
            section__neighborhood = vote['section__neighborhood']
            section__neighborhood_name = vote['section__neighborhood__name']
            total_neighborhood_votes = total_neighborhoods_votes.get(
                section__neighborhood=section__neighborhood)['total']
            votes_by_neighborhood.append({
                'total_votes': total_value,
                'neighborhood': section__neighborhood_name,
                'ruesp_can': round(total_value / total_political_parties_votes, 2),
                'rcan_uesp': round(total_value / total_neighborhood_votes, 2),
            })

        return Response(votes_by_neighborhood, status=status.HTTP_200_OK)


class ElectionResultsAV(APIView):
    def get(self, request, city, cargo, year):
        votes = Votes.objects.filter(political__political_type__id=int(cargo),
                                     political__region_id=int(city),
                                     political__election__year=int(year))

        votes_by_zone = {}
        zone_votes_id = []
        for vote in votes:
            if vote.zone.identifier in zone_votes_id:
                data_serialized = VotesSerializer(vote).data
                votes_by_zone[vote.zone.identifier]["data"].append(
                    data_serialized)
                votes_by_zone[vote.zone.identifier]["total_votes"] += + \
                    data_serialized["quantity"]

            else:
                zone_votes_id.append(vote.zone.identifier)
                data_serialized = VotesSerializer(vote).data
                votes_by_zone[vote.zone.identifier] = {
                    'data': [], 'total_votes': 0}
                votes_by_zone[vote.zone.identifier]["data"] = [data_serialized]
                votes_by_zone[vote.zone.identifier]["total_votes"] = data_serialized["quantity"]

        for zone_in in zone_votes_id:
            votes_by_zone[zone_in]["data"].sort(
                key=lambda x: x['quantity'], reverse=True)
            total_votes = votes_by_zone[zone_in]["total_votes"]
            for obj in votes_by_zone[zone_in]["data"]:
                obj['percentage'] = round(obj['quantity'] / total_votes, 2)

            votes_by_zone[zone_in]["data"] = votes_by_zone[zone_in]["data"][:5]

        return Response(votes_by_zone, status=status.HTTP_200_OK)
