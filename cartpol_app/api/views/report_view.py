from cartpol_app.scripts.report.run_report import run_report
from cartpol_app.models import Political, Votes, County, Neighborhood
from wsgiref.util import FileWrapper
from django.template.loader import render_to_string
from django.db.models import Sum, Subquery
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

    def get(self, request, year, political_id):
        
        # Inicando variáveis
        votes_by_neighborhood = []
        total_candidate_votes_queryset = []
        total_place_votes_queryset = []
        
        local_reference_name = ''
        
        should_search_state_id = request.query_params.get('state_id', False)
        should_search_county_id = request.query_params.get('county_id', False)
                
        political = get_object_or_404(Political, pk=political_id)
        
        political_filter = Political.objects.filter(
                political_type=political.political_type,
                election=political.election
            ).values('id')
        
        # Coletando queryset de votos por estado ou município
                
        if should_search_state_id:
            local_reference_name = 'section__neighborhood__county__name'
            county_filter = County.objects.filter(state=should_search_state_id).values('id')

            total_place_votes_queryset = Votes.objects \
                .filter(
                    political_id__in=Subquery(political_filter),
                    section__neighborhood__county_id__in=Subquery(county_filter)
                ) \
                .values(local_reference_name) \
                .annotate(total=Sum('quantity')) \
                .order_by('-total')
                
            total_candidate_votes_queryset = Votes.objects \
                .filter(
                    political_id=political.id,
                    section__neighborhood__county_id__in=Subquery(county_filter)
                ) \
                .values(local_reference_name) \
                .annotate(total=Sum('quantity')) \
                .order_by('-total')

        if should_search_county_id:
            local_reference_name = 'section__neighborhood__map_neighborhood'
            neighborhood_filter = Neighborhood.objects.filter(
                county=should_search_county_id
            ).values('id')
            
            total_place_votes_queryset = Votes.objects \
                .filter(
                    political_id__in=Subquery(political_filter),
                    section__neighborhood_id__in=Subquery(neighborhood_filter)
                ) \
                .values(local_reference_name) \
                .annotate(total=Sum('quantity'))
            
            total_candidate_votes_queryset = Votes.objects\
                .filter(
                    political_id=political.id,
                    section__neighborhood_id__in=Subquery(neighborhood_filter)
                ) \
                .values(local_reference_name)\
                .annotate(total=Sum('quantity'))\
                .order_by('-total')
                
        # Calculando distribuição de votos por bairro ou municipio
        total_place_votes_dict = {
            item[local_reference_name]: {
                'total': item['total'],
                'order': index+1,
                } for index, item in enumerate(total_place_votes_queryset)}
        
        total_place_votes = sum(item['total']
                                for item in total_place_votes_dict.values())
        
        total_candidate_votes = total_candidate_votes_queryset\
            .aggregate(Sum('total'))['total__sum']
       
        for vote in total_candidate_votes_queryset:
            total_value = vote['total']
            local_name = vote[local_reference_name]
            total_neighborhood_votes = total_place_votes_dict[local_name]['total']

            ruesp_can = round(total_value / total_candidate_votes, 6)
            rcan_uesp = round(total_value / total_neighborhood_votes, 6)
            ruesp = round(total_neighborhood_votes / total_place_votes, 6)

            votes_by_neighborhood.append({
                'total_votes': total_value,
                'neighborhood': local_name,
                'ruesp_can': round(ruesp_can*100, 2),
                'rcan_uesp': round(rcan_uesp*100, 2),
                'ruesp': round(ruesp*100, 2),
                'ruesp_position': total_place_votes_dict[local_name]['order']
            })
            
        top15rcan_uesp = sorted(votes_by_neighborhood, key=lambda x: x['rcan_uesp'], reverse=True)[:15]
        top15ruesp_can = sorted(votes_by_neighborhood, key=lambda x: x['ruesp_can'], reverse=True)[:15]
                
        # Gerando PDF
        
        font_config = FontConfiguration()
        filename = f'Relatório Cartpol - {political.name}'
        
        context = {"name": political.name, "year": year,
                   "filename": filename,
                   "partido": political.political_party.name,
                   "political_type": political.political_type.name,
                   "top15rcan_uesp": top15rcan_uesp,
                   "top15ruesp_can": top15ruesp_can}

        pdf_html = render_to_string(
            './reports/pages/index.html', context=context)

        html = HTML(string=pdf_html,
                    base_url=request.build_absolute_uri())
        
        css = CSS(filename='./cartpol_app/api/templates/css/index.css',
                  font_config=font_config)
        path = './reports_generated/example.pdf'


        html.write_pdf(path, stylesheets=[css],
                       font_config=font_config)
        report = open(path, 'rb')
        
        # return render(request, './reports/pages/index.html', context=context)
        return HttpResponse(FileWrapper(report), headers={
            "Content-Type": "application/pdf",
            "Content-Disposition": f'filename="{filename}.pdf"',
            })
