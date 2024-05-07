from django.db.models import Sum
from django.http import (
    HttpResponse,
)
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from wsgiref.util import FileWrapper

from cartpol_app.models import Votes, Political

from cartpol_app.scripts.report.run_report import run_report

class GenerateReportView(APIView):
    def post(self, request, cargo, year, political_id):
        political = Political.objects.get(id=political_id, political_type=cargo, election__year=year)
        county_id = political.region_id
        total_candidate_votes = Votes.objects\
            .filter(political_id=int(political_id))\
            .values('section__neighborhood', 'section__neighborhood__name')\
            .annotate(total_votes=Sum('quantity'))
        
        total_votes = Votes.objects.filter(political_id=int(political_id)).aggregate(Sum('quantity'))
        total_county_votes = Votes.objects.filter(section__neighborhood__county_id=county_id).aggregate(Sum('quantity'))
        total_neighborhoods_votes = Votes.objects.values('section__neighborhood').annotate(total=Sum('quantity'))

        votes_by_neighborhood = []
        
        total_candidates_votes = total_votes.get("quantity__sum")
        total_county_votes = total_county_votes.get("quantity__sum")
            
        for vote in total_candidate_votes:
            total_value = vote['total_votes']
            section__neighborhood = vote['section__neighborhood']
            section__neighborhood_name = vote['section__neighborhood__name']
            total_neighborhood_votes = total_neighborhoods_votes.get(section__neighborhood=section__neighborhood)['total']
            votes_by_neighborhood.append({
                    'neighborhood': section__neighborhood_name,
                    'total_votes': total_value, 
                    'dispersion': round(total_value  * 100.0 / total_county_votes, 2),
                    'concentration': round(total_value * 100.0 / total_candidates_votes, 2),
                    'dominance':  round(total_value * 100.0 / total_neighborhood_votes, 2)
                })
        
        data_adapted = []
        for vote in votes_by_neighborhood:
            data_adapted.append([vote['neighborhood'], vote['total_votes'], vote['dispersion'], vote['concentration'], vote['dominance']])
        
        path='/Users/iuri.felix/TCC/cartpol/reports_generated/report' + str(political_id) + '.pdf'

        
        run_report(data_adapted, path, political.name, True)
        report = open(path, 'rb')
        return HttpResponse(FileWrapper(report), content_type='application/pdf')
