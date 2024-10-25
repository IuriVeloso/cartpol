from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from cartpol_app.models import State, County, Neighborhood, ElectoralZone, PoliticalType, PoliticalParty, Election, Political, Votes
from cartpol_app.api.serializers import StateSerializer, CountySerializer, NeighborhoodSerializer, ElectoralZoneSerializer, PoliticalTypeSerializer, PoliticalPartySerializer, ElectionSerializer, PoliticalSerializer, VotesSerializer, VotesResultSerializer

class StateAV(APIView):
    def get(self, request):
        states = State.objects.all()
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
        county_serializer = CountySerializer(counties, many=True)
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
        neighborhood_serializer = NeighborhoodSerializer(neighborhoods, many=True)
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
        electoral_zone_serializer = ElectoralZoneSerializer(electoral_zones, many=True)
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
        political_type_serializer = PoliticalTypeSerializer(political_types, many=True)
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
        political_party_serializer = PoliticalPartySerializer(political_parties, many=True)
        return Response(political_party_serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        political_party_serializer = PoliticalPartySerializer(data=request.data)
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
        political_serializer = PoliticalSerializer(politicals, many=True)
        return Response(political_serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        political_serializer = PoliticalSerializer(data=request.data)
        if political_serializer.is_valid():
            political_serializer.save()
            return Response(political_serializer.data, status=status.HTTP_201_CREATED)
        return Response(political_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VotesAV(APIView):
    def get(self, request):
        votes = Votes.objects.all()
        votes_serializer = VotesSerializer(votes, many=True)
        return Response(votes_serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        votes_serializer = VotesSerializer(data=request.data)
        if votes_serializer.is_valid():
            votes_serializer.save()
            return Response(votes_serializer.data, status=status.HTTP_201_CREATED)
        return Response(votes_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
                votes_by_zone[vote.zone.identifier]["data"].append(data_serialized)
                votes_by_zone[vote.zone.identifier]["total_votes"] += + data_serialized["quantity"]
                
            else:
                zone_votes_id.append(vote.zone.identifier)
                data_serialized = VotesSerializer(vote).data
                print(data_serialized)
                votes_by_zone[vote.zone.identifier] = {'data': [], 'total_votes': 0}
                votes_by_zone[vote.zone.identifier]["data"] = [data_serialized]
                votes_by_zone[vote.zone.identifier]["total_votes"] = data_serialized["quantity"]


        for zone_in in zone_votes_id:
            votes_by_zone[zone_in]["data"].sort(key=lambda x: x['quantity'], reverse=True)
            total_votes = votes_by_zone[zone_in]["total_votes"]
            for obj in votes_by_zone[zone_in]["data"]:
                obj['percentage'] = round(obj['quantity'] * 100.0 / total_votes, 2)
            
            votes_by_zone[zone_in]["data"] = votes_by_zone[zone_in]["data"][:5]
                        
        return Response(votes_by_zone, status=status.HTTP_200_OK)
