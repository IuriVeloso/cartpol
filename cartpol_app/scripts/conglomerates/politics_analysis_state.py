"""
Análise de concentração política (fuzzy) agregada por município, para eleição estadual/federal.

Diferença em relação a `politics_analysis.py`:
- Unidade espacial: município (`County`) em vez de `map_neighborhood`;
- Totais da região: estado inteiro em vez de um único município;
- Vizinhança: JSON gerado por `build_county_neighbors_from_shapefile.py` (chaves = id de County).

Uso:
    python politics_analysis_state.py --political-id 17502 --qe 143852 \\
        --neighbors-json neighbors_mg_municipios.json \\
        [--threshold-percent 0.05]
"""

import argparse
import importlib.util
import json
import os
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cartpol.settings')

import django
from django.db.models import Sum

django.setup()

from cartpol_app.models import County, Political, VotesInNeighborhood

FUZZY_DIR = os.path.normpath(os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..', 'fuzzy_logic'))
fuzzy_module_path = os.path.join(FUZZY_DIR, 'fuzzy_cartpol.py')
spec = importlib.util.spec_from_file_location(
    "fuzzy_cartpol", fuzzy_module_path)
fuzzy_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fuzzy_module)
SistemaFuzzyMamdani = fuzzy_module.SistemaFuzzyMamdani

from politics_analysis import (
    classify_conglomerate_importance,
    classify_neighborhood_count,
    filter_significant_votes,
    find_filtered_conglomerates,
    interpret_concentration,
    load_neighbors_json,
)


def get_votes_by_county(
    political: Political
) -> Tuple[Dict[str, int], int]:
    votes = (
        VotesInNeighborhood.objects
        .filter(political=political)
        .values('neighborhood__county_id')
        .annotate(total_votes=Sum('quantity'))
    )
    votes_dict: Dict[str, int] = {}
    total = 0
    for v in votes:
        cid = v['neighborhood__county_id']
        if cid is None:
            continue
        key = str(cid)
        votes_dict[key] = v['total_votes']
        total += v['total_votes']
    return votes_dict, total


def get_total_votes_by_county_in_state(
    state_id: int
) -> Tuple[Dict[str, int], int]:
    votes = (
        VotesInNeighborhood.objects
        .filter(neighborhood__county__state_id=state_id)
        .values('neighborhood__county_id')
        .annotate(total_votes=Sum('quantity'))
    )
    total_votes_dict: Dict[str, int] = {}
    total_place = 0
    for v in votes:
        cid = v['neighborhood__county_id']
        if cid is None:
            continue
        key = str(cid)
        total_votes_dict[key] = v['total_votes']
        total_place += v['total_votes']
    return total_votes_dict, total_place


def get_total_counties_in_state(state_id: int) -> int:
    return County.objects.filter(state_id=state_id).count()


def resolve_state_id(political: Political, state_id_cli: Optional[int]) -> int:
    if state_id_cli is not None:
        return state_id_cli
    if political.region == 'state':
        return political.region_id
    first = (
        VotesInNeighborhood.objects
        .filter(political=political)
        .select_related('neighborhood__county')
        .first()
    )
    if first and first.neighborhood and first.neighborhood.county:
        return first.neighborhood.county.state_id
    raise ValueError(
        'Não foi possível determinar o estado. Passe --state-id ou garanta '
        'region="state" e region_id corretos no político.'
    )


def county_names_map(state_id: int) -> Dict[str, str]:
    rows = County.objects.filter(state_id=state_id).values_list('id', 'name')
    return {str(pk): name for pk, name in rows}


def calculate_conglomerate_indicators_municipios(
    conglomerate: Set[str],
    votes_dict: Dict[str, int],
    total_votes_dict: Dict[str, int],
    total_political_votes: int,
    total_place_votes: int,
    names: Dict[str, str],
) -> Dict[str, Any]:
    conglomerate_votes = sum(
        votes_dict.get(mid, 0) for mid in conglomerate
    )
    conglomerate_total_votes = sum(
        total_votes_dict.get(mid, 0) for mid in conglomerate
    )
    ruesp_can = (
        conglomerate_votes / total_political_votes
        if total_political_votes > 0 else 0
    )
    rcan_uesp = (
        conglomerate_votes / conglomerate_total_votes
        if conglomerate_total_votes > 0 else 0
    )
    ruesp = (
        conglomerate_total_votes / total_place_votes
        if total_place_votes > 0 else 0
    )
    sorted_ids = sorted(conglomerate, key=lambda x: int(x))
    return {
        'municipio_ids': sorted_ids,
        'municipio_nomes': [names.get(mid, mid) for mid in sorted_ids],
        'size': len(conglomerate),
        'total_votes': conglomerate_votes,
        'ruesp': round(ruesp, 6),
        'ruesp_can': round(ruesp_can, 6),
        'rcan_uesp': round(rcan_uesp, 6),
    }


def analyze_state_concentration(
    political_id: int,
    qe: float,
    neighbors_json_path: str,
    state_id: Optional[int] = None,
    output_path: Optional[str] = None,
    threshold_percent: float = 0.05,
    quiet: bool = False,
) -> Dict[str, Any]:
    def p(*args, **kwargs):
        if not quiet:
            print(*args, **kwargs)

    p(f"\n{'='*60}")
    p('ANÁLISE DE CONCENTRAÇÃO POLÍTICA (ESTADUAL / MUNICÍPIOS)')
    p(f"{'='*60}\n")

    try:
        political = Political.objects.get(id=political_id)
    except Political.DoesNotExist:
        raise ValueError(f'Político com ID {political_id} não encontrado')

    sid = resolve_state_id(political, state_id)
    names = county_names_map(sid)

    p(f'Político: {political.name}')
    p(f'Partido: {political.political_party.name}')
    p(f'Eleição: {political.election.year}')
    p(f'Estado (County.state_id): {sid}')
    p(f'Quociente Eleitoral: {qe}')

    p('\nBuscando votos por município...')
    votes_dict, total_political_votes = get_votes_by_county(political)
    p(f'  - Municípios com votos: {len(votes_dict)}')
    p(f'  - Total de votos do candidato: {total_political_votes}')

    total_votes_dict, total_place_votes = get_total_votes_by_county_in_state(sid)
    total_municipios = get_total_counties_in_state(sid)
    p(f'  - Municípios no estado (cadastro): {total_municipios}')
    p(f'  - Total de votos no estado (soma registros): {total_place_votes}')

    p(f'\nCarregando vizinhança de: {neighbors_json_path}')
    neighbors = load_neighbors_json(neighbors_json_path)
    p(f'  - Municípios no JSON: {len(neighbors)}')

    min_votes_effective = qe * threshold_percent
    min_votes_threshold = qe * 0.01
    filtered_votes = filter_significant_votes(
        votes_dict, qe, threshold_percent=threshold_percent)
    p(
        f'\nFiltro 1 - Votação Significativa (> {min_votes_effective:.0f} votos, '
        f'{threshold_percent * 100:.2f}% do QE):')
    p(f'  - Municípios antes: {len(votes_dict)}')
    p(f'  - Municípios depois: {len(filtered_votes)}')

    classification = classify_neighborhood_count(
        len(filtered_votes), total_municipios)
    pct = len(filtered_votes) / total_municipios * 100 if total_municipios else 0
    p('\nFiltro 2 - Classificação de municípios:')
    p(f'  - Percentual: {pct:.1f}%')
    p(f'  - Classificação: {classification}')

    filtered_ids = set(filtered_votes.keys())
    conglomerates = find_filtered_conglomerates(filtered_ids, neighbors)
    p(f'\nConglomerados identificados: {len(conglomerates)}')

    p('\nCalculando indicadores e concentração fuzzy...')
    fuzzy_dir = os.path.join(os.path.dirname(__file__), '..', 'fuzzy_logic')
    sf = SistemaFuzzyMamdani(
        arq_variaveis=os.path.join(fuzzy_dir, 'variaveis-fuzzy.json'),
        arq_regras=os.path.join(fuzzy_dir, 'regras-fuzzy.json'),
        defuzz='centroide',
    )

    conglomerate_results = []
    fuzzy_results = []
    qe_normalized = qe / total_place_votes if total_place_votes > 0 else 0

    for i, conglomerate in enumerate(conglomerates, 1):
        indicators = calculate_conglomerate_indicators_municipios(
            conglomerate, filtered_votes, total_votes_dict,
            total_political_votes, total_place_votes, names,
        )
        importance = classify_conglomerate_importance(
            indicators['ruesp'], qe_normalized)
        indicators['importance'] = importance

        entradas = {
            'ruesp_can': indicators['ruesp_can'] * 100,
            'tam_conglomerado': min(indicators['size'], 10),
            'qtd_bairros': min(len(filtered_votes), 100),
        }
        try:
            fuzzy_concentration = sf.inferir(entradas)
        except Exception as e:
            p(f'  Aviso: Erro no cálculo fuzzy do conglomerado {i}: {e}')
            fuzzy_concentration = 0.0

        indicators['fuzzy_concentration'] = round(fuzzy_concentration, 4)
        indicators['id'] = i
        fuzzy_results.append(fuzzy_concentration)
        conglomerate_results.append(indicators)

        p(
            f'  Conglomerado {i}: {indicators["size"]} municípios, '
            f'RUESP_CAN={indicators["ruesp_can"]:.4f}, '
            f'Fuzzy={fuzzy_concentration:.4f}'
        )

    concentracao_final = (
        sum(fuzzy_results) / len(fuzzy_results) if fuzzy_results else 0.0
    )

    p(f"\n{'='*60}")
    p('RESULTADO FINAL')
    p(f"{'='*60}")
    p(f'Concentração Final (média): {concentracao_final:.4f}')
    p(f'Interpretação: {interpret_concentration(concentracao_final)}')

    result = {
        'political': {
            'id': political.id,
            'name': political.name,
            'full_name': political.full_name,
            'party': political.political_party.name,
            'total_votes': total_political_votes,
        },
        'parameters': {
            'QE': qe,
            'state_id': sid,
            'neighbors_json': neighbors_json_path,
            'threshold_percent': threshold_percent,
        },
        'filtering': {
            'total_municipios_in_state': total_municipios,
            'municipios_with_votes': len(votes_dict),
            'municipios_after_filter': len(filtered_votes),
            'classification': classification,
            'min_votes_threshold': min_votes_threshold,
            'min_votes_effective_filter': min_votes_effective,
        },
        'conglomerates': conglomerate_results,
        'summary': {
            'total_conglomerates': len(conglomerates),
            'fuzzy_results': [round(r, 4) for r in fuzzy_results],
            'concentracao_final': round(concentracao_final, 4),
            'interpretation': interpret_concentration(concentracao_final),
        },
    }

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        p(f'\nResultado salvo em: {output_path}')

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Analisa concentração política (fuzzy) por município no estado'
    )
    parser.add_argument('--political-id', type=int, required=True)
    parser.add_argument('--qe', type=float, required=True)
    parser.add_argument('--neighbors-json', type=str, required=True)
    parser.add_argument('--state-id', type=int, default=None,
                        help='ID do State no banco (se não for inferido)')
    parser.add_argument(
        '--threshold-percent',
        type=float,
        default=0.05,
        help='Fração do QE para filtrar municípios (padrão 0.05 = 5%%). '
        'Em agregação estadual, 5%% costuma ser muito alto; reduza se necessário.',
    )
    parser.add_argument('--output', type=str, default=None)
    args = parser.parse_args()

    try:
        result = analyze_state_concentration(
            political_id=args.political_id,
            qe=args.qe,
            neighbors_json_path=args.neighbors_json,
            state_id=args.state_id,
            output_path=args.output,
            threshold_percent=args.threshold_percent,
            quiet=False,
        )
        if not args.output:
            print('\n' + json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f'\nErro: {e}')
        raise


if __name__ == '__main__':
    main()
