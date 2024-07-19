from django.db.models import Sum
from rest_framework import status
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
        states = State.objects.all()
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
        counties = County.objects.all()
        should_search_county = request.query_params.get('name', False)
        should_search_state = request.query_params.get('state', False)
        should_search_tse_id = request.query_params.get('state', False)
        if should_search_state:
            counties = counties.filter(state__name=should_search_state)
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
        if should_search_neighborhood:
            neighborhoods = neighborhoods.filter(
                name=should_search_neighborhood)
        if should_search_county:
            neighborhoods = neighborhoods.filter(
                county__name=should_search_county)

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
        should_search_county = request.query_params.get('county', False)

        if should_search_electoral_zone:
            electoral_zones = electoral_zones.filter(
                identifier=should_search_electoral_zone)
        if should_search_county:
            electoral_zones = electoral_zones.filter(
                county__name=should_search_county)

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
        political_types = PoliticalType.objects.all()
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
        elections = Election.objects.all()
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
        politicals = Political.objects.all()

        should_search_political_code = request.query_params.get(
            'political_code', False)
        should_search_full_name = request.query_params.get('full_name', False)
        if should_search_full_name:
            politicals = politicals.filter(full_name=should_search_full_name)
        if should_search_political_code:
            politicals = politicals.filter(
                political_code=should_search_political_code)

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
    def get(self, request):
        sections = Section.objects.all()

        should_search_county = request.query_params.get('county', False)
        should_search_county_tse_id = request.query_params.get(
            'county_tse_id', False)
        should_search_electoral_zone = request.query_params.get(
            'electoral_zone', False)
        should_search_identifier = request.query_params.get(
            'identifier', False)
        if should_search_county:
            sections = sections.filter(
                neighborhood__county__name=should_search_county)
        if should_search_electoral_zone:
            sections = sections.filter(
                electoral_zone__identifier=should_search_electoral_zone)
        if should_search_identifier:
            sections = sections.filter(identifier=should_search_identifier)
        if should_search_county_tse_id:
            sections = sections.filter(identifier=should_search_county_tse_id)

        section_serializer = SectionSerializer(sections, many=True)
        return Response(section_serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        section_serializer = SectionSerializer(
            data=request.data, many=isinstance(request.data, list))
        if section_serializer.is_valid():
            section_serializer.save()
            return Response(section_serializer.data, status=status.HTTP_201_CREATED)
        return Response(section_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PoliticalVotesAV(APIView):
    def get(self, request, political_id):
        # FIXME - Remove this county id and use the value from the route (Also update docs)
        total_candidate_votes = Votes.objects\
            .filter(political_id=int(political_id))\
            .values('section__neighborhood', 'section__neighborhood__name')\
            .annotate(total_votes=Sum('quantity'))

        political = Political.objects.get(id=int(political_id))

        total_votes = Votes.objects.filter(
            political_id=int(political_id)).aggregate(Sum('quantity'))
        total_neighborhoods_votes = Votes.objects.values(
            'section__neighborhood').annotate(total=Sum('quantity'))

        total_political_votes = total_votes.get("quantity__sum")

        print(political, total_political_votes)

        votes_by_neighborhood = []

        for vote in total_candidate_votes:
            total_value = vote['total_votes']
            section__neighborhood = vote['section__neighborhood']
            section__neighborhood_name = vote['section__neighborhood__name']
            total_neighborhood_votes = total_neighborhoods_votes.get(
                section__neighborhood=section__neighborhood)['total']
            votes_by_neighborhood.append({
                'total_votes': total_value,
                'neighborhood': section__neighborhood_name,
                'ruesp_can': round(total_value / total_political_votes, 6),
                'rcan_uesp': round(total_value / total_neighborhood_votes, 6),
            })

        return Response(votes_by_neighborhood, status=status.HTTP_200_OK)


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
