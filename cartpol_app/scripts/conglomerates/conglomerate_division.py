"""
Módulo para análise de conglomerados espaciais em shapefiles.

Este módulo identifica quais regiões (bairros, municípios, etc.) são vizinhas
dentro de um shapefile, permitindo análises de contiguidade espacial.
"""

import argparse
import json
import os
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

import geopandas as gpd
import pandas as pd


def load_shapefile(shapefile_path: str) -> gpd.GeoDataFrame:
    """
    Carrega um shapefile a partir do caminho fornecido.

    Args:
        shapefile_path: Caminho para o shapefile (.shp, .zip, ou diretório)

    Returns:
        GeoDataFrame com os dados do shapefile

    Raises:
        FileNotFoundError: Se o arquivo não existir
        ValueError: Se o arquivo não for um shapefile válido
    """
    import zipfile

    if not os.path.exists(shapefile_path):
        raise FileNotFoundError(f"Shapefile não encontrado: {shapefile_path}")

    # Converter para caminho absoluto
    abs_path = os.path.abspath(shapefile_path)

    # Detectar tipo de arquivo e carregar apropriadamente
    if abs_path.endswith('.zip'):
        # Verificar estrutura do zip para encontrar o .shp
        with zipfile.ZipFile(abs_path, 'r') as zf:
            shp_files = [f for f in zf.namelist() if f.endswith('.shp')]
            if not shp_files:
                raise ValueError(f"Nenhum arquivo .shp encontrado no zip: {abs_path}")
            # Usar o primeiro .shp encontrado
            shp_file = shp_files[0]
            print(f"Arquivo shapefile encontrado no zip: {shp_file}")

        # Carregar usando o caminho completo dentro do zip
        gdf = gpd.read_file(f"zip://{abs_path}!{shp_file}")
    else:
        gdf = gpd.read_file(abs_path)

    print(f"Shapefile carregado: {shapefile_path}")
    print(f"  - Total de features: {len(gdf)}")
    print(f"  - Colunas: {list(gdf.columns)}")
    print(f"  - CRS: {gdf.crs}")

    return gdf


def get_name_column(gdf: gpd.GeoDataFrame) -> str:
    """
    Identifica automaticamente a coluna de nome no GeoDataFrame.

    Args:
        gdf: GeoDataFrame do shapefile

    Returns:
        Nome da coluna identificada

    Raises:
        ValueError: Se nenhuma coluna de nome for encontrada
    """
    # Colunas possíveis para identificação de regiões
    possible_name_cols = [
        'NM_BAIRRO', 'NOME', 'BAIRRO', 'bairro', 'nome', 'NAME',
        'NM_DIST', 'DISTRITO', 'distrito', 'NM_MUN', 'MUNICIPIO',
        'NM_REGIAO', 'REGIAO', 'NM_UF', 'SIGLA_UF', 'CD_GEOCMU',
        'CD_MUN', 'CD_GEOCODM', 'GEOCODIGO', 'ID', 'FID', 'OBJECTID'
    ]

    for col in possible_name_cols:
        if col in gdf.columns:
            print(f"  - Coluna de identificação encontrada: {col}")
            return col

    # Se não encontrar, usar a primeira coluna que não seja geometry
    non_geom_cols = [c for c in gdf.columns if c != 'geometry']
    if non_geom_cols:
        print(f"  - Usando primeira coluna disponível: {non_geom_cols[0]}")
        return non_geom_cols[0]

    raise ValueError("Não foi possível identificar coluna de nome no shapefile")


def calculate_neighbors(
    gdf: gpd.GeoDataFrame,
    name_column: Optional[str] = None,
    method: str = 'touches'
) -> Dict[str, List[str]]:
    """
    Calcula os vizinhos de cada região no shapefile.

    Args:
        gdf: GeoDataFrame com as geometrias
        name_column: Coluna para identificar cada região (auto-detecta se None)
        method: Método de vizinhança:
            - 'touches': Regiões que se tocam (compartilham borda)
            - 'intersects': Regiões que se intersectam (inclui sobreposição)
            - 'queen': Vizinhança Queen (compartilham borda ou vértice)

    Returns:
        Dicionário onde chaves são nomes de regiões e valores são
        listas de nomes de regiões vizinhas
    """
    if name_column is None:
        name_column = get_name_column(gdf)

    print(f"\nCalculando vizinhos usando método '{method}'...")

    neighbors: Dict[str, List[str]] = defaultdict(list)
    n_features = len(gdf)

    # Criar índice espacial para otimização
    sindex = gdf.sindex

    for idx, row in gdf.iterrows():
        region_name = str(row[name_column])
        geom = row.geometry

        if geom is None or geom.is_empty:
            print(f"  - Aviso: Geometria vazia para '{region_name}'")
            continue

        # Usar índice espacial para encontrar candidatos
        possible_matches_idx = list(sindex.intersection(geom.bounds))

        for other_idx in possible_matches_idx:
            if other_idx == idx:
                continue

            other_row = gdf.iloc[other_idx]
            other_name = str(other_row[name_column])
            other_geom = other_row.geometry

            if other_geom is None or other_geom.is_empty:
                continue

            # Verificar vizinhança conforme método escolhido
            is_neighbor = False
            if method == 'touches':
                is_neighbor = geom.touches(other_geom) or (
                    geom.intersects(other_geom) and
                    not geom.within(other_geom) and
                    not other_geom.within(geom)
                )
            elif method == 'intersects':
                is_neighbor = geom.intersects(other_geom)
            elif method == 'queen':
                # Queen: compartilha pelo menos um ponto
                is_neighbor = geom.touches(other_geom) or geom.intersects(
                    other_geom
                )

            if is_neighbor and other_name not in neighbors[region_name]:
                neighbors[region_name].append(other_name)

    # Ordenar vizinhos para consistência
    for region in neighbors:
        neighbors[region].sort()

    print(f"  - Vizinhança calculada para {len(neighbors)} regiões")

    return dict(neighbors)


def find_conglomerates(
    neighbors: Dict[str, List[str]]
) -> List[Set[str]]:
    """
    Identifica conglomerados (componentes conectados) no grafo de vizinhança.

    Um conglomerado é um grupo de regiões onde todas estão conectadas
    direta ou indiretamente através de relações de vizinhança.

    Args:
        neighbors: Dicionário de vizinhança

    Returns:
        Lista de conjuntos, onde cada conjunto é um conglomerado
    """
    print("\nIdentificando conglomerados...")

    visited: Set[str] = set()
    conglomerates: List[Set[str]] = []

    def dfs(region: str, current_cluster: Set[str]):
        """Busca em profundidade para encontrar componentes conectados."""
        if region in visited:
            return
        visited.add(region)
        current_cluster.add(region)

        for neighbor in neighbors.get(region, []):
            if neighbor not in visited:
                dfs(neighbor, current_cluster)

    # Adicionar todas as regiões (mesmo as sem vizinhos)
    all_regions = set(neighbors.keys())
    for region_list in neighbors.values():
        all_regions.update(region_list)

    for region in all_regions:
        if region not in visited:
            current_cluster: Set[str] = set()
            dfs(region, current_cluster)
            if current_cluster:
                conglomerates.append(current_cluster)

    # Ordenar por tamanho (maior primeiro)
    conglomerates.sort(key=len, reverse=True)

    print(f"  - Total de conglomerados encontrados: {len(conglomerates)}")
    for i, cluster in enumerate(conglomerates[:5]):
        print(f"    - Conglomerado {i+1}: {len(cluster)} regiões")

    if len(conglomerates) > 5:
        print(f"    - ... e mais {len(conglomerates) - 5} conglomerados")

    return conglomerates


def get_neighbor_statistics(
    neighbors: Dict[str, List[str]]
) -> Dict[str, any]:
    """
    Calcula estatísticas sobre a vizinhança.

    Args:
        neighbors: Dicionário de vizinhança

    Returns:
        Dicionário com estatísticas
    """
    if not neighbors:
        return {
            'total_regions': 0,
            'total_neighbors': 0,
            'avg_neighbors': 0,
            'max_neighbors': 0,
            'min_neighbors': 0,
            'isolated_regions': 0
        }

    neighbor_counts = [len(v) for v in neighbors.values()]

    stats = {
        'total_regions': len(neighbors),
        'total_neighbors': sum(neighbor_counts) // 2,  # Cada par conta 2x
        'avg_neighbors': sum(neighbor_counts) / len(neighbors),
        'max_neighbors': max(neighbor_counts),
        'min_neighbors': min(neighbor_counts),
        'isolated_regions': sum(1 for v in neighbors.values() if len(v) == 0)
    }

    # Encontrar regiões com mais e menos vizinhos
    if neighbors:
        max_region = max(neighbors.keys(), key=lambda k: len(neighbors[k]))
        min_region = min(neighbors.keys(), key=lambda k: len(neighbors[k]))
        stats['region_most_neighbors'] = max_region
        stats['region_least_neighbors'] = min_region

    return stats


def analyze_shapefile_conglomerates(
    shapefile_path: str,
    name_column: Optional[str] = None,
    method: str = 'touches',
    output_json: Optional[str] = None
) -> Tuple[Dict[str, List[str]], List[Set[str]], Dict]:
    """
    Função principal para analisar conglomerados em um shapefile.

    Args:
        shapefile_path: Caminho para o shapefile
        name_column: Coluna de identificação das regiões
        method: Método de cálculo de vizinhança
        output_json: Caminho para salvar resultados em JSON (opcional)

    Returns:
        Tupla com (dicionário de vizinhos, lista de conglomerados, estatísticas)
    """
    print(f"\n{'='*60}")
    print("ANÁLISE DE CONGLOMERADOS ESPACIAIS")
    print(f"{'='*60}\n")

    # Carregar shapefile
    gdf = load_shapefile(shapefile_path)

    # Calcular vizinhos
    neighbors = calculate_neighbors(gdf, name_column, method)

    # Encontrar conglomerados
    conglomerates = find_conglomerates(neighbors)

    # Calcular estatísticas
    stats = get_neighbor_statistics(neighbors)

    # Exibir resumo
    print(f"\n{'='*60}")
    print("RESUMO DA ANÁLISE")
    print(f"{'='*60}")
    print(f"Total de regiões: {stats['total_regions']}")
    print(f"Total de relações de vizinhança: {stats['total_neighbors']}")
    print(f"Média de vizinhos por região: {stats['avg_neighbors']:.2f}")
    print(f"Máximo de vizinhos: {stats['max_neighbors']}")
    print(f"Mínimo de vizinhos: {stats['min_neighbors']}")
    print(f"Regiões isoladas: {stats['isolated_regions']}")
    print(f"Conglomerados identificados: {len(conglomerates)}")

    if 'region_most_neighbors' in stats:
        most = stats['region_most_neighbors']
        print(f"Região com mais vizinhos: {most} ({len(neighbors[most])} vizinhos)")

    # Salvar em JSON se solicitado
    if output_json:
        result = {
            'shapefile': shapefile_path,
            'method': method,
            'statistics': stats,
            'neighbors': neighbors,
            'conglomerates': [list(c) for c in conglomerates]
        }

        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"\nResultados salvos em: {output_json}")

    return neighbors, conglomerates, stats


def create_neighbor_matrix(
    gdf: gpd.GeoDataFrame,
    name_column: Optional[str] = None,
    method: str = 'touches'
) -> pd.DataFrame:
    """
    Cria uma matriz de adjacência para as regiões do shapefile.

    Args:
        gdf: GeoDataFrame com as geometrias
        name_column: Coluna para identificar cada região
        method: Método de vizinhança

    Returns:
        DataFrame com matriz de adjacência (1 = vizinho, 0 = não vizinho)
    """
    if name_column is None:
        name_column = get_name_column(gdf)

    neighbors = calculate_neighbors(gdf, name_column, method)

    # Obter todas as regiões
    all_regions = sorted(set(neighbors.keys()) | {
        n for ns in neighbors.values() for n in ns
    })

    # Criar matriz
    matrix = pd.DataFrame(0, index=all_regions, columns=all_regions)

    for region, region_neighbors in neighbors.items():
        for neighbor in region_neighbors:
            matrix.loc[region, neighbor] = 1
            matrix.loc[neighbor, region] = 1  # Matriz simétrica

    return matrix


def get_neighbors_of_region(
    neighbors: Dict[str, List[str]],
    region_name: str,
    order: int = 1
) -> Set[str]:
    """
    Obtém os vizinhos de uma região até uma determinada ordem.

    Args:
        neighbors: Dicionário de vizinhança
        region_name: Nome da região
        order: Ordem da vizinhança (1 = vizinhos diretos, 2 = vizinhos de vizinhos)

    Returns:
        Conjunto de regiões vizinhas até a ordem especificada
    """
    if region_name not in neighbors:
        return set()

    result: Set[str] = set()
    current_level: Set[str] = {region_name}

    for _ in range(order):
        next_level: Set[str] = set()
        for region in current_level:
            next_level.update(neighbors.get(region, []))
        result.update(next_level)
        current_level = next_level - result

    result.discard(region_name)  # Remover a própria região
    return result


def main():
    """Função principal para execução via linha de comando."""
    parser = argparse.ArgumentParser(
        description='Analisa conglomerados espaciais em shapefiles'
    )
    parser.add_argument(
        'shapefile',
        type=str,
        help='Caminho para o shapefile (.shp ou .zip)'
    )
    parser.add_argument(
        '--name-column',
        type=str,
        default=None,
        help='Coluna para identificar regiões (auto-detecta se não fornecido)'
    )
    parser.add_argument(
        '--method',
        type=str,
        choices=['touches', 'intersects', 'queen'],
        default='touches',
        help='Método de cálculo de vizinhança (padrão: touches)'
    )
    parser.add_argument(
        '--output-json',
        type=str,
        default=None,
        help='Caminho para salvar resultados em JSON'
    )
    parser.add_argument(
        '--show-neighbors',
        type=str,
        default=None,
        help='Mostra vizinhos de uma região específica'
    )
    parser.add_argument(
        '--neighbor-order',
        type=int,
        default=1,
        help='Ordem da vizinhança para --show-neighbors (padrão: 1)'
    )

    args = parser.parse_args()

    # Executar análise
    neighbors, conglomerates, stats = analyze_shapefile_conglomerates(
        args.shapefile,
        args.name_column,
        args.method,
        args.output_json
    )

    # Mostrar vizinhos de região específica se solicitado
    if args.show_neighbors:
        region_neighbors = get_neighbors_of_region(
            neighbors, args.show_neighbors, args.neighbor_order
        )
        print(f"\nVizinhos de '{args.show_neighbors}' (ordem {args.neighbor_order}):")
        for neighbor in sorted(region_neighbors):
            print(f"  - {neighbor}")


if __name__ == '__main__':
    main()


# Exemplo de uso programático:
'''
from conglomerate_division import (
    analyze_shapefile_conglomerates,
    load_shapefile,
    calculate_neighbors,
    find_conglomerates,
    create_neighbor_matrix,
    get_neighbors_of_region
)

# Análise completa
neighbors, conglomerates, stats = analyze_shapefile_conglomerates(
    'Rio de Janeiro.zip',
    output_json='rj_conglomerates.json'
)

# Ou uso individual das funções:
gdf = load_shapefile('Rio de Janeiro.zip')
neighbors = calculate_neighbors(gdf, name_column='NM_BAIRRO', method='touches')
conglomerates = find_conglomerates(neighbors)

# Criar matriz de adjacência
matrix = create_neighbor_matrix(gdf)
print(matrix)

# Obter vizinhos de segunda ordem de uma região
vizinhos_2nd_order = get_neighbors_of_region(neighbors, 'Centro', order=2)
'''
