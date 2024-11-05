from cartpol_app.scripts.report.run_report import run_report
from cartpol_app.models import Political, Votes
from wsgiref.util import FileWrapper
from django.template.loader import render_to_string
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from rest_framework.views import APIView
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration


class GenerateReportView(APIView):
    def post(self, request, cargo, year, political_id):
        political = get_object_or_404(Political, pk=political_id)
        county_id = political.region_id

        total_candidate_votes = Votes.objects\
            .filter(political_id=int(political_id))\
            .values('section__neighborhood__name')\
            .annotate(total_votes=Sum('quantity'))

        total_votes = Votes.objects.filter(
            political_id=int(political_id)).aggregate(Sum('quantity'))

        total_neighborhoods_votes = Votes.objects \
            .filter(political__political_type=political.political_type,
                    political__election=political.election,
                    political__region_id=political.region_id) \
            .values('section__neighborhood__name') \
            .annotate(total=Sum('quantity'))

        total_neighborhoods_votes_dict = {
            item['section__neighborhood__name']: item['total'] for item in total_neighborhoods_votes}

        total_place_votes = sum(item['total']
                                for item in total_neighborhoods_votes)

        total_political_votes = total_votes.get("quantity__sum")

        votes_by_neighborhood = []
        data_adapted = []

        for vote in total_candidate_votes:
            total_value = vote['total_votes']
            section__neighborhood_name = vote['section__neighborhood__name']
            total_neighborhood_votes = total_neighborhoods_votes_dict[section__neighborhood_name]

            ruesp_can = round(total_value / total_political_votes, 6)
            rcan_uesp = round(total_value / total_neighborhood_votes, 6)
            ruesp = round(total_neighborhood_votes / total_place_votes, 6)

            votes_by_neighborhood.append({
                'neighborhood': section__neighborhood_name,
                'total_votes': total_value,
                'rcan_uesp': rcan_uesp,
                'ruesp_can': ruesp_can,
                'ruesp':  ruesp
            })
            data_adapted.append([section__neighborhood_name, total_value,
                                rcan_uesp, ruesp_can, ruesp])

        path = '/home/iurivfelix/TCC/cartpol/reports_generated/report' + \
            str(political_id) + '.pdf'

        run_report(data_adapted, path, political.name,
                   str(political.political_code), True)
        report = open(path, 'rb')
        return HttpResponse(FileWrapper(report), content_type='application/pdf')

    def get(self, request, cargo, year, political_id):
        font_config = FontConfiguration()
        context = {"name": "Candidato Fantasma", "year": 2022,
                   "partido": "PPP", "political_type": "Deputado Estadual"}

        pdf_html = render_to_string(
            './reports/pages/index.html', context=context)

        html = HTML(string=pdf_html)
        css = CSS(filename='./cartpol_app/api/templates/css/index.css',
                  font_config=font_config)
        path = './reports_generated/example.pdf'

        html.write_pdf(path, stylesheets=[css],
                       font_config=font_config)
        report = open(path, 'rb')
        # return render(request, './reports/pages/index.html', context=context)
        return HttpResponse(FileWrapper(report), content_type='application/pdf')
