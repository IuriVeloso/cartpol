from rest_framework import serializers;
from cartpol_app.models import State, County, Neighborhood, ElectoralZone, PoliticalType, PoliticalParty, Election, Political, Votes, Section

class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model= State
        fields='__all__'
        
class CountySerializer(serializers.ModelSerializer):
    class Meta:
        model = County
        fields = '__all__'
        
class NeighborhoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Neighborhood
        fields = '__all__'
        
class ElectoralZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElectoralZone
        fields = '__all__'
        
class PoliticalTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PoliticalType
        fields = '__all__'
        
class PoliticalPartySerializer(serializers.ModelSerializer):
    class Meta:
        model = PoliticalParty
        fields = '__all__'
        
class ElectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Election
        fields = '__all__'
        
class PoliticalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Political
        fields = '__all__'
        
class VotesSerializer(serializers.ModelSerializer):
    political_name = serializers.SerializerMethodField(source='political.name', read_only=True)
    political_party_name = serializers.CharField(source='political.political_party.name', read_only=True)
    
    def get_political_name(self, obj):
        return str.title(obj.political.name)
        
    class Meta:
        model = Votes
        fields = '__all__'
        
class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = '__all__' 
        
class VotesResultSerializer(serializers.ModelSerializer):
    percentage = serializers.FloatField()
    class Meta:
        model = Votes
        fields = ['political', 'quantity', 'description', 'percentage']
