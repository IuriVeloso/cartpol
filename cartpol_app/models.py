from django.core.exceptions import ValidationError
from django.db import models

# Create your models here.


def validate_list(value):
    if value not in ['federal', 'state', 'city']:
        raise ValidationError(
            ('%(value)s must be one of "["federal", "state", "city"]"'),
            params={'value': value}
        )


class State (models.Model):
    name = models.CharField(max_length=8)
    full_name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class County (models.Model):
    name = models.CharField(max_length=40)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    tse_id = models.IntegerField()

    def __str__(self):
        return self.name


class Neighborhood (models.Model):
    name = models.CharField(max_length=100)
    county = models.ForeignKey(County, on_delete=models.CASCADE)
    map_neighborhood = models.CharField(max_length=100, default='', blank=True)

    def __str__(self):
        return self.name


class ElectoralZone (models.Model):
    identifier = models.CharField(max_length=40)
    county = models.ForeignKey(County, on_delete=models.CASCADE)
    year = models.IntegerField()

    def __str__(self):
        return self.identifier


class Section (models.Model):
    identifier = models.CharField(max_length=40)
    cep = models.CharField(max_length=10, default='')
    address = models.CharField(max_length=100, default='')
    electoral_zone = models.ForeignKey(ElectoralZone, on_delete=models.CASCADE)
    neighborhood = models.ForeignKey(Neighborhood, on_delete=models.CASCADE)

    def __str__(self):
        return self.identifier


class PoliticalParty (models.Model):
    name = models.CharField(max_length=40)
    full_name = models.CharField(max_length=200)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Election (models.Model):
    year = models.IntegerField()
    round = models.IntegerField()
    code = models.IntegerField()


class PoliticalType (models.Model):
    name = models.CharField(max_length=40)
    description = models.CharField(max_length=200)
    election = models.ForeignKey(Election, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Political (models.Model):
    name = models.CharField(max_length=100)
    full_name = models.CharField(max_length=200)
    political_party = models.ForeignKey(
        PoliticalParty, on_delete=models.CASCADE)
    political_type = models.ForeignKey(PoliticalType, on_delete=models.CASCADE)
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    region = models.CharField(max_length=50, validators=[validate_list])
    region_id = models.IntegerField()
    political_code = models.IntegerField()

    def __str__(self):
        return self.name



class Votes (models.Model):
    quantity = models.IntegerField()
    political = models.ForeignKey(Political, on_delete=models.CASCADE)
    description = models.CharField(max_length=200)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)

    def __votes__(self):
        return self.quantity
    

