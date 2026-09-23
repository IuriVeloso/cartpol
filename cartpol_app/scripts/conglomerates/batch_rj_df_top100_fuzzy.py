"""
Lê os 100 Deputados Federais com mais votos no Rio de Janeiro (eleição configurável),
roda `analyze_state_concentration` para cada um e grava um CSV.

Filtro (conforme models.Political):
  - political_type__name == 'Deputado Federal'
  - election__year == <ano>
  - region == 'state'   (candidaturas proporcionais usam UF como estado)
  - region_id == State.id do RJ

QE padrão: soma de todos os votos em VotesInNeighborhood desses candidatos no RJ,
dividido por 46 (vagas de DF no RJ em 2022). Pode ser sobrescrito com --qe.

Uso:
    cd /home/iuri/TCC/cartpol && .venv/bin/python \\
      cartpol_app/scripts/conglomerates/batch_rj_df_top100_fuzzy.py \\
      --neighbors-json cartpol_app/scripts/conglomerates/neighbors_rj_municipios.json \\
      --output cartpol_app/scripts/conglomerates/rj_df_top100_fuzzy_2022.csv
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

from cartpol_app.models import Political, State, VotesInNeighborhood

from politics_analysis_state import analyze_state_concentration


def _default_neighbors_path() -> str:
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'neighbors_rj_municipios.json',
    )


def _compute_default_qe(state_id: int, year: int, vagas: int) -> float:
    total = (
        VotesInNeighborhood.objects.filter(
            political__political_type__name='Deputado Federal',
            political__election__year=year,
            political__region='state',
            political__region_id=state_id,
        ).aggregate(t=Sum('quantity'))['t']
    )
    total = total or 0
    if vagas <= 0:
        raise ValueError('vagas deve ser > 0')
    return float(total) / float(vagas)


def _summarize_conglomerates(result: Dict[str, Any], max_items: int = 8) -> str:
    cong: List[Dict[str, Any]] = result.get('conglomerates') or []
    if not cong:
        return ''
    ranked = sorted(
        cong,
        key=lambda c: (c.get('size', 0), c.get('total_votes', 0)),
        reverse=True,
    )[:max_items]
    parts = []
    for i, c in enumerate(ranked, 1):
        n = c.get('size', 0)
        v = c.get('total_votes', 0)
        fz = c.get('fuzzy_concentration', '')
        nomes = c.get('municipio_nomes') or []
        preview = ', '.join(nomes[:3])
        if len(nomes) > 3:
            preview += '...'
        parts.append(f'#{i}(n={n},v={v},fuzzy={fz}):{preview}')
    return ' | '.join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(
        description='CSV fuzzy por município — top 100 DF RJ'
    )
    parser.add_argument('--year', type=int, default=2022)
    parser.add_argument('--limit', type=int, default=100)
    parser.add_argument('--vagas', type=int, default=46,
                        help='Vagas de deputado federal no RJ (2022: 46)')
    parser.add_argument(
        '--qe',
        type=float,
        default=None,
        help='QE explícito; se omitido, calcula a partir da soma de votos DF RJ / vagas',
    )
    parser.add_argument(
        '--neighbors-json',
        default=_default_neighbors_path(),
        help='JSON de vizinhança entre municípios (County.id)',
    )
    parser.add_argument(
        '--threshold-percent',
        type=float,
        default=0.0002,
        help='Fração do QE para filtrar municípios (lote; padrão 0.02%% do QE)',
    )
    parser.add_argument('--output', required=True, help='Arquivo CSV de saída')
    args = parser.parse_args()

    rj = State.objects.get(name='RJ')
    state_id = rj.id

    qe = args.qe if args.qe is not None else _compute_default_qe(
        state_id, args.year, args.vagas
    )

    candidates = (
        Political.objects.filter(
            political_type__name='Deputado Federal',
            election__year=args.year,
            region='state',
            region_id=state_id,
        )
        .select_related('political_party', 'election')
        .annotate(total_votes=Sum('votesinneighborhood__quantity'))
        .order_by('-total_votes')[: args.limit]
    )

    out_dir = os.path.dirname(os.path.abspath(args.output))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    fieldnames = [
        'id',
        'candidato',
        'partido',
        'ano',
        'total_votos',
        'qe_usado',
        'threshold_percent',
        'concentracao_fuzzy',
        'interpretacao',
        'num_conglomerados',
        'municipios_apos_filtro',
        'resumo_conglomerados',
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
                'ano': pol.election.year,
                'total_votos': pol.total_votes or 0,
                'qe_usado': round(qe, 4),
                'threshold_percent': args.threshold_percent,
                'concentracao_fuzzy': '',
                'interpretacao': '',
                'num_conglomerados': '',
                'municipios_apos_filtro': '',
                'resumo_conglomerados': '',
                'erro': '',
            }
            try:
                result = analyze_state_concentration(
                    political_id=pol.id,
                    qe=qe,
                    neighbors_json_path=args.neighbors_json,
                    state_id=state_id,
                    output_path=None,
                    threshold_percent=args.threshold_percent,
                    quiet=True,
                )
                row['concentracao_fuzzy'] = result['summary']['concentracao_final']
                row['interpretacao'] = result['summary']['interpretation']
                row['num_conglomerados'] = result['summary']['total_conglomerates']
                row['municipios_apos_filtro'] = result['filtering'][
                    'municipios_after_filter'
                ]
                row['resumo_conglomerados'] = _summarize_conglomerates(result)
            except Exception as e:
                row['erro'] = str(e)

            w.writerow(row)
            print(f'[{idx}/{args.limit}] id={pol.id} {pol.name[:40]} ok' if not row['erro'] else f'[{idx}] id={pol.id} ERRO {row["erro"]}')

    meta_path = args.output.replace('.csv', '_meta.json')
    meta = {
        'filtro': {
            'cargo': 'Deputado Federal',
            'uf': 'RJ',
            'state_id': state_id,
            'ano': args.year,
            'limite': args.limit,
            'region': 'state',
            'region_id': state_id,
        },
        'qe': qe,
        'vagas': args.vagas,
        'threshold_percent': args.threshold_percent,
        'neighbors_json': os.path.abspath(args.neighbors_json),
        'csv': os.path.abspath(args.output),
    }
    with open(meta_path, 'w', encoding='utf-8') as fm:
        json.dump(meta, fm, ensure_ascii=False, indent=2)
    print(f'Meta: {meta_path}')
    print(f'CSV: {args.output}')


if __name__ == '__main__':
    main()
