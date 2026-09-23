"""
Módulo para análise de concentração política usando lógica fuzzy.

Este módulo analisa a distribuição de votos de um político por bairros,
identifica conglomerados espaciais e aplica lógica fuzzy para determinar
o nível de concentração de votos.
"""

import argparse
import importlib.util
import json
import os
import sys
from typing import Any, Dict, List, Set, Tuple

# Adicionar diretório raiz ao path
BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Configuração do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cartpol.settings')


import django
from django.db.models import Sum

django.setup()

from cartpol_app.models import (County, Neighborhood, Political,
                                VotesInNeighborhood)


# Importar sistema fuzzy usando importlib para evitar problemas de path
FUZZY_DIR = os.path.normpath(os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..', 'fuzzy_logic'))
fuzzy_module_path = os.path.join(FUZZY_DIR, 'fuzzy_cartpol.py')
spec = importlib.util.spec_from_file_location(
    "fuzzy_cartpol", fuzzy_module_path)
fuzzy_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fuzzy_module)
SistemaFuzzyMamdani = fuzzy_module.SistemaFuzzyMamdani


def load_neighbors_json(json_path: str) -> Dict[str, List[str]]:
    """
    Carrega o arquivo JSON com as relações de vizinhança.

    Args:
        json_path: Caminho para o arquivo JSON

    Returns:
        Dicionário de vizinhança {bairro: [lista de vizinhos]}
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('neighbors', {})


def get_votes_by_map_neighborhood(
    political: Political
) -> Tuple[Dict[str, int], int]:
    """
    Busca votos agrupados por map_neighborhood.

    Args:
        political: Objeto Political do candidato

    Returns:
        Tupla com (dicionário de votos por bairro, total de votos do político)
    """
    votes = (
        VotesInNeighborhood.objects
        .filter(political=political)
        .values('neighborhood__map_neighborhood')
        .annotate(total_votes=Sum('quantity'))
    )

    votes_dict = {}
    total_political_votes = 0

    for v in votes:
        neighborhood_name = v['neighborhood__map_neighborhood']
        if neighborhood_name:  # Ignorar valores vazios
            votes_dict[neighborhood_name] = v['total_votes']
            total_political_votes += v['total_votes']

    return votes_dict, total_political_votes


def get_total_votes_by_neighborhood(
    county_id: int,
    election_id: int = None
) -> Tuple[Dict[str, int], int]:
    """
    Busca o total de votos (todos os candidatos) por bairro.

    Args:
        county_id: ID do município
        election_id: Se fornecido, filtra pela mesma eleição (para LQ/HC corretos)

    Returns:
        Tupla com (dicionário de votos totais por bairro, total geral)
    """
    qs = VotesInNeighborhood.objects.filter(
        neighborhood__county_id=county_id
    )
    if election_id is not None:
        qs = qs.filter(political__election_id=election_id)

    votes = qs.values('neighborhood__map_neighborhood').annotate(
        total_votes=Sum('quantity')
    )

    total_votes_dict = {}
    total_place_votes = 0

    for v in votes:
        neighborhood_name = v['neighborhood__map_neighborhood']
        if neighborhood_name:
            total_votes_dict[neighborhood_name] = v['total_votes']
            total_place_votes += v['total_votes']

    return total_votes_dict, total_place_votes


def calculate_lq_hc(
    votes_dict: Dict[str, int],
    total_votes_dict: Dict[str, int],
    total_political_votes: int,
    total_place_votes: int
) -> Dict[str, Dict[str, float]]:
    """
    Calcula LQ e HC por bairro (Silva & Davidian, BPSR 2013).

    LQ_im = (V_im / V_i) / (V_m / V)
    HC_im = (V_i * V_m / V) * (LQ_im - 1)

    Args:
        votes_dict: Votos do candidato por bairro {bairro: V_im}
        total_votes_dict: Votos totais por bairro {bairro: V_m}
        total_political_votes: V_i (total do candidato)
        total_place_votes: V (total geral da eleição no município)

    Returns:
        Dict {bairro: {'lq': float, 'hc': float}}
    """
    result = {}
    if total_political_votes == 0 or total_place_votes == 0:
        return result

    for neighborhood, v_im in votes_dict.items():
        v_m = total_votes_dict.get(neighborhood, 0)
        if v_m == 0:
            continue
        lq = (v_im / total_political_votes) / (v_m / total_place_votes)
        hc = (total_political_votes * v_m / total_place_votes) * (lq - 1)
        result[neighborhood] = {
            'lq': round(lq, 4),
            'hc': round(hc, 2)
        }

    return result


def get_total_neighborhoods_in_city(county_id: int) -> int:
    """
    Retorna o número total de bairros únicos (map_neighborhood) no município.

    Args:
        county_id: ID do município

    Returns:
        Número de bairros distintos
    """
    return (
        Neighborhood.objects
        .filter(county_id=county_id)
        .exclude(map_neighborhood='')
        .values('map_neighborhood')
        .distinct()
        .count()
    )


def filter_significant_votes(
    votes_dict: Dict[str, int],
    qe: float,
    total_neighborhoods: int,
    threshold_percent: float = 0.05
) -> Dict[str, int]:
    """
    Filtro 1: Votação Significativa.
    Mantém apenas bairros onde votos > threshold_percent * Q.E.

    Args:
        votes_dict: Dicionário de votos por bairro
        qe: Quociente Eleitoral
        threshold_percent: Percentual mínimo do Q.E. (padrão 5%)

    Returns:
        Dicionário filtrado
    """
    neighborhoods_denominator = max(int(total_neighborhoods or 0), 1)
    min_votes = (qe * threshold_percent) / neighborhoods_denominator
    return {
        neighborhood: votes
        for neighborhood, votes in votes_dict.items()
        if votes > min_votes
    }


def classify_neighborhood_count(
    filtered_count: int,
    total_count: int
) -> str:
    """
    Filtro 2: Classifica a quantidade de bairros.

    Args:
        filtered_count: Número de bairros após filtro
        total_count: Número total de bairros

    Returns:
        Classificação: 'P' (Pequeno), 'M' (Médio), 'G' (Grande)
    """
    if total_count == 0:
        return 'P'

    percentage = filtered_count / total_count

    if percentage < 0.20:
        return 'P'
    elif percentage <= 0.50:
        return 'M'
    else:
        return 'G'


def find_filtered_conglomerates(
    filtered_neighborhoods: Set[str],
    neighbors: Dict[str, List[str]]
) -> List[Set[str]]:
    """
    Encontra conglomerados (grupos conectados) dos bairros filtrados.

    Args:
        filtered_neighborhoods: Conjunto de bairros que passaram no filtro
        neighbors: Dicionário de vizinhança

    Returns:
        Lista de conjuntos, cada um representando um conglomerado
    """
    visited: Set[str] = set()
    conglomerates: List[Set[str]] = []

    def dfs(neighborhood: str, cluster: Set[str]):
        if neighborhood in visited:
            return
        if neighborhood not in filtered_neighborhoods:
            return

        visited.add(neighborhood)
        cluster.add(neighborhood)

        for neighbor in neighbors.get(neighborhood, []):
            if neighbor in filtered_neighborhoods and neighbor not in visited:
                dfs(neighbor, cluster)

    for neighborhood in filtered_neighborhoods:
        if neighborhood not in visited:
            cluster: Set[str] = set()
            dfs(neighborhood, cluster)
            if cluster:
                conglomerates.append(cluster)

    # Ordenar por tamanho (maior primeiro)
    conglomerates.sort(key=len, reverse=True)

    return conglomerates


def calculate_conglomerate_indicators(
    conglomerate: Set[str],
    votes_dict: Dict[str, int],
    total_votes_dict: Dict[str, int],
    total_political_votes: int,
    total_place_votes: int
) -> Dict[str, Any]:
    """
    Calcula RUESP, RUESP_CAN e RCAN_UESP para um conglomerado.

    Args:
        conglomerate: Conjunto de bairros do conglomerado
        votes_dict: Votos do candidato por bairro
        total_votes_dict: Votos totais por bairro
        total_political_votes: Total de votos do candidato
        total_place_votes: Total de votos na região

    Returns:
        Dicionário com indicadores do conglomerado
    """
    # Somar votos do candidato no conglomerado
    conglomerate_votes = sum(
        votes_dict.get(neighborhood, 0)
        for neighborhood in conglomerate
    )

    # Somar votos totais no conglomerado
    conglomerate_total_votes = sum(
        total_votes_dict.get(neighborhood, 0)
        for neighborhood in conglomerate
    )

    # Calcular indicadores
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

    return {
        'neighborhoods': sorted(list(conglomerate)),
        'size': len(conglomerate),
        'total_votes': conglomerate_votes,
        'ruesp': round(ruesp, 6),
        'ruesp_can': round(ruesp_can, 6),
        'rcan_uesp': round(rcan_uesp, 6)
    }


def classify_conglomerate_importance(ruesp: float, qe_normalized: float) -> str:
    """
    Filtro 3: Classifica importância do conglomerado.

    Args:
        ruesp: RUESP do conglomerado
        qe_normalized: Q.E. normalizado (como proporção)

    Returns:
        'P' (Pequeno) ou 'G' (Grande)
    """
    return 'G' if ruesp > qe_normalized else 'P'


def _summarize_lq_hc(lq_hc: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    """Resumo agregado de LQ e HC para o candidato."""
    if not lq_hc:
        return {}
    lq_max_bairro = max(lq_hc, key=lambda k: lq_hc[k]['lq'])
    hc_positivo = sum(v['hc'] for v in lq_hc.values() if v['hc'] > 0)
    return {
        'lq_max': lq_hc[lq_max_bairro]['lq'],
        'bairro_lq_max': lq_max_bairro,
        'hc_total_positivo': round(hc_positivo, 2),
        'bairros_lq_acima_1': sum(1 for v in lq_hc.values() if v['lq'] > 1),
    }


def interpret_concentration(value: float) -> str:
    """
    Interpreta o valor de concentração fuzzy.

    Args:
        value: Valor de concentração (0-1)

    Returns:
        Interpretação textual
    """
    if value < 0.125:
        return 'irrisoria'
    elif value < 0.25:
        return 'muito_baixa'
    elif value < 0.375:
        return 'baixa'
    elif value < 0.5:
        return 'media_baixa'
    elif value < 0.625:
        return 'media'
    elif value < 0.75:
        return 'media_alta'
    elif value < 0.875:
        return 'alta'
    elif value < 1.0:
        return 'muito_alta'
    else:
        return 'altissima'


def analyze_political_concentration(
    political_id: int,
    qe: float,
    neighbors_json_path: str,
    output_path: str = None,
    threshold_percent: float = 0.05,
) -> Dict[str, Any]:
    """
    Função principal de análise de concentração política.

    Args:
        political_id: ID do político no banco de dados
        qe: Quociente Eleitoral
        neighbors_json_path: Caminho para o JSON de vizinhança
        output_path: Caminho para salvar resultado (opcional)

    Returns:
        Dicionário com análise completa
    """
    print(f"\n{'='*60}")
    print("ANÁLISE DE CONCENTRAÇÃO POLÍTICA")
    print(f"{'='*60}\n")

    # 1. Carregar político
    try:
        political = Political.objects.get(id=political_id)
    except Political.DoesNotExist:
        raise ValueError(f"Político com ID {political_id} não encontrado")

    print(f"Político: {political.name}")
    print(f"Partido: {political.political_party.name}")
    print(f"Eleição: {political.election.year}")
    print(f"Quociente Eleitoral: {qe}")

    # 2. Buscar votos agrupados por map_neighborhood
    print("\nBuscando votos por bairro...")
    votes_dict, total_political_votes = get_votes_by_map_neighborhood(
        political)
    print(f"  - Bairros com votos: {len(votes_dict)}")
    print(f"  - Total de votos: {total_political_votes}")

    # 3. Buscar votos totais por bairro (todos os candidatos na mesma eleição)
    county_id = political.region_id
    total_votes_dict, total_place_votes = get_total_votes_by_neighborhood(
        county_id, election_id=political.election_id)
    total_neighborhoods = get_total_neighborhoods_in_city(county_id)
    print(f"  - Total de bairros na cidade: {total_neighborhoods}")
    print(f"  - Total de votos na região: {total_place_votes}")

    # 3b. Calcular LQ e HC por bairro (Silva & Davidian, BPSR 2013)
    lq_hc_by_neighborhood = calculate_lq_hc(
        votes_dict, total_votes_dict, total_political_votes, total_place_votes
    )

    # 4. Carregar vizinhança
    print(f"\nCarregando vizinhança de: {neighbors_json_path}")
    neighbors = load_neighbors_json(neighbors_json_path)
    print(f"  - Bairros no JSON: {len(neighbors)}")

    # 5. Filtro 1: Votação Significativa (> threshold_percent * Q.E.)
    min_votes_threshold = (qe * threshold_percent) / max(int(total_neighborhoods or 0), 1)
    filtered_votes = filter_significant_votes(
        votes_dict, qe, total_neighborhoods, threshold_percent
    )
    print(
        f"\nFiltro 1 - Votação Significativa (> {min_votes_threshold:.0f} votos):")
    print(f"  - Bairros antes: {len(votes_dict)}")
    print(f"  - Bairros depois: {len(filtered_votes)}")

    # 6. Filtro 2: Classificação de quantidade de bairros
    classification = classify_neighborhood_count(
        len(filtered_votes), total_neighborhoods)
    print(f"\nFiltro 2 - Classificação de Bairros:")
    print(
        f"  - Percentual: {len(filtered_votes)/total_neighborhoods*100:.1f}%")
    print(f"  - Classificação: {classification}")

    # 7. Identificar conglomerados
    filtered_neighborhoods = set(filtered_votes.keys())
    conglomerates = find_filtered_conglomerates(
        filtered_neighborhoods, neighbors)
    print(f"\nConglomerados identificados: {len(conglomerates)}")

    # 8. Calcular indicadores e aplicar fuzzy para cada conglomerado
    print("\nCalculando indicadores e concentração fuzzy...")

    # Inicializar sistema fuzzy
    fuzzy_dir = os.path.join(os.path.dirname(__file__), '..', 'fuzzy_logic')
    sf = SistemaFuzzyMamdani(
        arq_variaveis=os.path.join(fuzzy_dir, 'variaveis-fuzzy.json'),
        arq_regras=os.path.join(fuzzy_dir, 'regras-fuzzy.json'),
        defuzz="centroide"
    )

    conglomerate_results = []
    fuzzy_results = []
    qe_normalized = qe / total_place_votes if total_place_votes > 0 else 0

    for i, conglomerate in enumerate(conglomerates, 1):
        # Calcular indicadores
        indicators = calculate_conglomerate_indicators(
            conglomerate, filtered_votes, total_votes_dict,
            total_political_votes, total_place_votes
        )

        # Classificar importância
        importance = classify_conglomerate_importance(
            indicators['ruesp'], qe_normalized)
        indicators['importance'] = importance

        # Aplicar lógica fuzzy
        entradas = {
            "ruesp_can": indicators['ruesp_can'] * 100,  # Converter para %
            # Limitar ao domínio
            "tam_conglomerado": min(indicators['size'], 10),
            "qtd_bairros": min(len(filtered_votes), 100)  # Limitar ao domínio
        }

        try:
            fuzzy_concentration = sf.inferir(entradas)
        except Exception as e:
            print(f"  Aviso: Erro no cálculo fuzzy do conglomerado {i}: {e}")
            fuzzy_concentration = 0.0

        indicators['fuzzy_concentration'] = round(fuzzy_concentration, 4)
        indicators['id'] = i
        fuzzy_results.append(fuzzy_concentration)

        conglomerate_results.append(indicators)

        print(f"  Conglomerado {i}: {indicators['size']} bairros, "
              f"RUESP_CAN={indicators['ruesp_can']:.4f}, "
              f"Fuzzy={fuzzy_concentration:.4f}")

    # 9. Calcular média aritmética dos resultados fuzzy
    concentracao_final = (
        sum(fuzzy_results) / len(fuzzy_results)
        if fuzzy_results else 0.0
    )

    print(f"\n{'='*60}")
    print("RESULTADO FINAL")
    print(f"{'='*60}")
    print(f"Concentração Final (média): {concentracao_final:.4f}")
    print(f"Interpretação: {interpret_concentration(concentracao_final)}")

    # 10. Montar resultado
    result = {
        "political": {
            "id": political.id,
            "name": political.name,
            "full_name": political.full_name,
            "party": political.political_party.name,
            "total_votes": total_political_votes
        },
        "parameters": {
            "QE": qe,
            "neighbors_json": neighbors_json_path
        },
        "filtering": {
            "total_neighborhoods_in_city": total_neighborhoods,
            "neighborhoods_with_votes": len(votes_dict),
            "neighborhoods_after_filter": len(filtered_votes),
            "classification": classification,
            "min_votes_threshold": min_votes_threshold
        },
        "conglomerates": conglomerate_results,
        "lq_hc": lq_hc_by_neighborhood,
        "lq_hc_summary": _summarize_lq_hc(lq_hc_by_neighborhood),
        "summary": {
            "total_conglomerates": len(conglomerates),
            "fuzzy_results": [round(r, 4) for r in fuzzy_results],
            "concentracao_final": round(concentracao_final, 4),
            "interpretation": interpret_concentration(concentracao_final)
        }
    }

    # 11. Salvar se caminho fornecido
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\nResultado salvo em: {output_path}")

    return result


def main():
    """Função principal para execução via linha de comando."""
    parser = argparse.ArgumentParser(
        description='Analisa concentração política usando lógica fuzzy'
    )
    parser.add_argument(
        '--political-id',
        type=int,
        required=True,
        help='ID do político no banco de dados'
    )
    parser.add_argument(
        '--qe',
        type=float,
        required=True,
        help='Quociente Eleitoral'
    )
    parser.add_argument(
        '--neighbors-json',
        type=str,
        required=True,
        help='Caminho para o arquivo JSON de vizinhança'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Caminho para salvar o resultado em JSON'
    )

    args = parser.parse_args()

    try:
        result = analyze_political_concentration(
            political_id=args.political_id,
            qe=args.qe,
            neighbors_json_path=args.neighbors_json,
            output_path=args.output
        )

        if not args.output:
            print("\n" + json.dumps(result, ensure_ascii=False, indent=2))

    except Exception as e:
        print(f"\nErro: {e}")
        raise


if __name__ == '__main__':
    main()
