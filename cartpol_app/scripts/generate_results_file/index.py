import os
import django
import csv
from django.db import models

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cartpol_app.settings')
django.setup()

from cartpol_app.models import Political, Votes, Section, County, Election, PoliticalType, PoliticalParty, State, Neighborhood


year = 2024
state_name = 'RJ'

# Filtra o State RJ e Election 2020
election = Election.objects.get(year=year)
state = State.objects.get(name=state_name)

# Busca todos os counties do RJ
counties = County.objects.filter(state=state)

# Prepara lista de resultados
results = []

# Calcula o total de votos no estado (RJ, 2020)
all_sections = Section.objects.filter(electoral_zone__county__in=counties)
votes_estado = Votes.objects.filter(section__in=all_sections, political__election=election)
total_votos_estado = votes_estado.aggregate(total=models.Sum('quantity'))['total'] or 0

# Calcula o total de votos por candidato no estado
votos_por_candidato_estado = votes_estado.values('political').annotate(total=models.Sum('quantity'))
votos_candidato_dict = {v['political']: v['total'] for v in votos_por_candidato_estado}

# Calcula o total de votos por município
votos_por_municipio = votes_estado.values('section__electoral_zone__county').annotate(total=models.Sum('quantity'))
votos_municipio_dict = {v['section__electoral_zone__county']: v['total'] for v in votos_por_municipio}

if year in [2020, 2024]:
    # Para cada município
    for county in counties:
        # Busca todos os bairros do município
        neighborhoods = Neighborhood.objects.filter(county=county)
        # Busca todas as sections do município
        sections_county = Section.objects.filter(electoral_zone__county=county)
        # Total de votos no município
        votes_county = Votes.objects.filter(section__in=sections_county, political__election=election)
        total_votos_county = votes_county.aggregate(total=models.Sum('quantity'))['total'] or 1

        # Total de votos por candidato no município
        votos_por_candidato_county = votes_county.values('political').annotate(total=models.Sum('quantity'))
        votos_candidato_county_dict = {v['political']: v['total'] for v in votos_por_candidato_county}

        for neighborhood in neighborhoods:
            # Busca todas as sections do bairro
            sections_neigh = Section.objects.filter(electoral_zone__county=county, neighborhood=neighborhood)
            # Votos no bairro
            votes_neigh = Votes.objects.filter(section__in=sections_neigh, political__election=election)
            # Total de votos no bairro
            total_votos_neigh = votes_neigh.aggregate(total=models.Sum('quantity'))['total'] or 0

            # Total de votos por candidato no bairro
            votos_por_candidato_neigh = votes_neigh.values('political').annotate(total=models.Sum('quantity'))
            votos_candidato_neigh_dict = {v['political']: v['total'] for v in votos_por_candidato_neigh}

            for pid, total_votes in votos_candidato_neigh_dict.items():
                political = Political.objects.get(id=pid)
                votos_candidato_municipio = votos_candidato_county_dict.get(pid, 0) or 1  # evita divisão por zero
                RCAN_UESP = total_votes / total_votos_county if total_votos_county else 0
                RUESP_CAN = total_votes / votos_candidato_municipio if votos_candidato_municipio else 0
                RUESP = total_votos_neigh / total_votos_county if total_votos_county else 0
                results.append({
                    'id_politico': political.id,
                    'nome_politico': political.name,
                    'nome_completo_politico': political.full_name,
                    'eleicao': political.election.year,
                    'tipo_politico': political.political_type.name,
                    'partido_politico': political.political_party.name,
                    'codigo_politico': political.political_code,
                    'municipio': county.name,
                    'bairro': neighborhood.name,
                    'votos': total_votes,
                    'RCAN_UESP': RCAN_UESP,
                    'RUESP_CAN': RUESP_CAN,
                    'RUESP': RUESP
                })
else:
    for county in counties:
        # Busca todas as sections desse county
        sections = Section.objects.filter(electoral_zone__county=county)
        # Busca todos os votos nessas sections
        votes = Votes.objects.filter(section__in=sections, political__election=election)
        # Agrupa por political
        political_ids = votes.values_list('political', flat=True).distinct()
        print(f'Processando município: {county.name} com {len(political_ids)} políticos.')
        for pid in political_ids:
            
            political = Political.objects.get(id=pid)
            total_votes = votes.filter(political=political).aggregate(total=models.Sum('quantity'))['total'] or 0
            # Calcula os indicadores
            votos_candidato_estado = votos_candidato_dict.get(political.id, 0) or 1  # evita divisão por zero
            votos_municipio = votos_municipio_dict.get(county.id, 0) or 1
            total_estado = total_votos_estado or 1
            RCAN_UESP = total_votes / total_estado
            RUESP_CAN = total_votes / votos_candidato_estado
            RUESP = votos_municipio / total_estado
            results.append({
                'id_politico': political.id,
                'nome_politico': political.name,
                'nome_completo_politico': political.full_name,
                'eleicao': political.election.year,
                'tipo_politico': political.political_type.name,
                'partido_politico': political.political_party.name,
                'codigo_politico': political.political_code,
                'municipio': county.name,
                'votos': total_votes,
                'RCAN_UESP': RCAN_UESP,
                'RUESP_CAN': RUESP_CAN,
                'RUESP': RUESP
            })

# Escreve o CSV
if year in [2020, 2024]:
    fieldnames = ['id_politico', 'nome_politico', 'nome_completo_politico', 'eleicao', 'tipo_politico', 'partido_politico', 'codigo_politico', 'municipio', 'bairro', 'votos', 'RCAN_UESP', 'RUESP_CAN', 'RUESP']
else:
    fieldnames = ['id_politico', 'nome_politico', 'nome_completo_politico', 'eleicao', 'tipo_politico', 'partido_politico', 'codigo_politico', 'municipio', 'votos', 'RCAN_UESP', 'RUESP_CAN', 'RUESP']

with open(f'results_rj_{year}.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
    writer.writeheader()
    for row in results:
        writer.writerow(row)

print(f'Arquivo results_rj_{year}.csv gerado com sucesso!')
