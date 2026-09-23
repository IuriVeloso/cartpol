"""
Roda analyze_political_concentration para vereadores de uma capital,
ordenados por votos, e grava CSV com fuzzy + LQ/HC.

Uso:
    cd /home/iuri/TCC/cartpol && .venv/bin/python
      cartpol_app/scripts/conglomerates/batch_vereadores_capital_fuzzy.py
      --city-name "Rio de Janeiro"
      --year 2024
      --qe 59154
      --neighbors-json cartpol_app/scripts/conglomerates/neighbors_rio_de_janeiro_bairros.json
      --output cartpol_app/scripts/conglomerates/vereadores_rj_2024.csv
"""

import argparse
import csv
import json
import os
import sys
from typing import Any, Dict, List

BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cartpol.settings')

import django
from django.db.models import Sum

django.setup()

from cartpol_app.models import County, Political

import importlib.util
_pa_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'politics_analysis.py')
_spec = importlib.util.spec_from_file_location('politics_analysis', _pa_path)
_pa = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_pa)
analyze_political_concentration = _pa.analyze_political_concentration


def _summarize_conglomerates(result: Dict[str, Any], max_items: int = 5) -> str:
    cong: List[Dict[str, Any]] = result.get('conglomerates') or []
    if not cong:
        return ''
    ranked = sorted(cong, key=lambda c: c.get('total_votes', 0), reverse=True)[:max_items]
    parts = []
    for i, c in enumerate(ranked, 1):
        n = c.get('size', 0)
        v = c.get('total_votes', 0)
        fz = c.get('fuzzy_concentration', '')
        nomes = c.get('neighborhoods') or []
        preview = ', '.join(nomes[:3])
        if len(nomes) > 3:
            preview += '...'
        parts.append(f'#{i}(n={n},v={v},fuzzy={fz}):{preview}')
    return ' | '.join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(
        description='CSV fuzzy + LQ/HC para vereadores de uma capital'
    )
    parser.add_argument('--city-name', required=True,
                        help='Nome do município (ex: "Rio de Janeiro")')
    parser.add_argument('--year', type=int, required=True,
                        help='Ano da eleição (ex: 2020 ou 2024)')
    parser.add_argument('--qe', type=float, required=True,
                        help='Quociente Eleitoral da eleição')
    parser.add_argument('--neighbors-json', required=True,
                        help='JSON de vizinhança de bairros da cidade')
    parser.add_argument('--threshold-percent', type=float, default=0.05,
                        help='Percentual mínimo do QE para filtrar bairros (padrão 5%%)')
    parser.add_argument('--limit', type=int, default=None,
                        help='Número máximo de candidatos (padrão: todos)')
    parser.add_argument('--vagas', type=int, default=None,
                        help='Número de vagas — processa apenas os top N eleitos por votos')
    parser.add_argument('--output', required=True, help='Arquivo CSV de saída')
    args = parser.parse_args()

    try:
        county = County.objects.get(name=args.city_name)
    except County.DoesNotExist:
        # Tentar busca parcial
        county = County.objects.filter(name__icontains=args.city_name).first()
        if county is None:
            raise ValueError(f"Município '{args.city_name}' não encontrado no banco")
        print(f"Município encontrado: {county.name} (id={county.id})")

    candidates = (
        Political.objects.filter(
            political_type__name='Vereador',
            election__year=args.year,
            region='city',
            region_id=county.id,
        )
        .select_related('political_party', 'election')
        .annotate(total_votes=Sum('votesinneighborhood__quantity'))
        .order_by('-total_votes')
    )

    n = args.vagas or args.limit or 80
    candidates = candidates[:n]

    total = candidates.count()
    print(f"Candidatos encontrados: {total} (top {n} por votos)")
    if total == 0:
        print("Nenhum candidato encontrado. Verifique city-name, year e dados no banco.")
        return

    out_dir = os.path.dirname(os.path.abspath(args.output))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    fieldnames = [
        'id', 'candidato', 'partido', 'cidade', 'ano', 'total_votos',
        'qe_usado', 'threshold_percent',
        'concentracao_fuzzy', 'interpretacao',
        'num_conglomerados', 'bairros_apos_filtro', 'resumo_conglomerados',
        'lq_max', 'bairro_lq_max', 'hc_total_positivo', 'bairros_lq_acima_1',
        'erro',
    ]

    with open(args.output, 'w', encoding='utf-8-sig', newline='') as fcsv:
        w = csv.DictWriter(fcsv, fieldnames=fieldnames)
        w.writeheader()

        for idx, pol in enumerate(candidates, 1):
            row = {
                'id': pol.id,
                'candidato': pol.name,
                'partido': pol.political_party.name,
                'cidade': county.name,
                'ano': pol.election.year,
                'total_votos': pol.total_votes or 0,
                'qe_usado': args.qe,
                'threshold_percent': args.threshold_percent,
                'concentracao_fuzzy': '',
                'interpretacao': '',
                'num_conglomerados': '',
                'bairros_apos_filtro': '',
                'resumo_conglomerados': '',
                'lq_max': '',
                'bairro_lq_max': '',
                'hc_total_positivo': '',
                'bairros_lq_acima_1': '',
                'erro': '',
            }
            try:
                result = analyze_political_concentration(
                    political_id=pol.id,
                    qe=args.qe,
                    neighbors_json_path=args.neighbors_json,
                    output_path=None,
                    threshold_percent=args.threshold_percent,
                )
                summary = result.get('summary', {})
                filtering = result.get('filtering', {})
                lq_hc_summary = result.get('lq_hc_summary', {})

                row['concentracao_fuzzy'] = summary.get('concentracao_final', '')
                row['interpretacao'] = summary.get('interpretation', '')
                row['num_conglomerados'] = summary.get('total_conglomerates', '')
                row['bairros_apos_filtro'] = filtering.get('neighborhoods_after_filter', '')
                row['resumo_conglomerados'] = _summarize_conglomerates(result)
                row['lq_max'] = lq_hc_summary.get('lq_max', '')
                row['bairro_lq_max'] = lq_hc_summary.get('bairro_lq_max', '')
                row['hc_total_positivo'] = lq_hc_summary.get('hc_total_positivo', '')
                row['bairros_lq_acima_1'] = lq_hc_summary.get('bairros_lq_acima_1', '')

                print(f"[{idx}/{total}] {pol.name[:40]} fuzzy={row['concentracao_fuzzy']} lq_max={row['lq_max']}")
            except Exception as e:
                row['erro'] = str(e)
                print(f"[{idx}/{total}] ERRO id={pol.id} {pol.name[:30]}: {e}")

            w.writerow(row)

    meta_path = args.output.replace('.csv', '_meta.json')
    meta = {
        'filtro': {
            'cargo': 'Vereador',
            'cidade': county.name,
            'county_id': county.id,
            'ano': args.year,
            'top_n': n,
        },
        'qe': args.qe,
        'threshold_percent': args.threshold_percent,
        'neighbors_json': os.path.abspath(args.neighbors_json),
        'csv': os.path.abspath(args.output),
    }
    with open(meta_path, 'w', encoding='utf-8') as fm:
        json.dump(meta, fm, ensure_ascii=False, indent=2)
    print(f'\nMeta: {meta_path}')
    print(f'CSV:  {args.output}')


if __name__ == '__main__':
    main()
