"""
Gera JSON de vizinhança entre bairros a partir de shapefile de cidade (zip).

As chaves do JSON são os nomes dos bairros (map_neighborhood), que devem
coincidir com os valores de Neighborhood.map_neighborhood no banco.

Uso:
    python build_neighborhood_neighbors_from_shapefile.py
        --shapefile-zip <zip>
        --output <json>
"""

import argparse
import json
import os
import sys
import tempfile
import zipfile

BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


def _detect_name_column(gdf) -> str:
    """Auto-detecta a coluna de nome do bairro no shapefile."""
    candidates = ['NM_BAIRRO', 'NOME', 'BAIRRO', 'NM_DIST', 'NOME_BAIRRO',
                  'NAME', 'nm_bairro', 'nome', 'bairro', 'name_distr', 'name_neigh']
    for col in candidates:
        if col in gdf.columns:
            # Pular colunas onde todos os valores são nulos ou repetidos (ex: name_neigh vazio)
            non_null = gdf[col].dropna()
            if len(non_null) > 0 and non_null.nunique() > 1:
                return col
    # Fallback: primeira coluna string com múltiplos valores únicos
    for col in gdf.columns:
        if col != 'geometry' and gdf[col].dtype == object:
            non_null = gdf[col].dropna()
            if len(non_null) > 0 and non_null.nunique() > 1:
                return col
    raise ValueError(f"Não foi possível detectar coluna de nome. Colunas: {list(gdf.columns)}")


def build_neighborhood_neighbors(zip_path: str) -> dict:
    """
    Lê o shapefile do zip e retorna dicionário de vizinhança.

    Returns:
        Dict com 'neighbors' (nome -> [nomes vizinhos]) e 'stats'
    """
    import geopandas as gpd

    with zipfile.ZipFile(zip_path) as zf:
        with tempfile.TemporaryDirectory() as tmp:
            zf.extractall(tmp)
            shp_files = [n for n in zf.namelist() if n.lower().endswith('.shp')]
            if not shp_files:
                raise FileNotFoundError(f"Nenhum .shp encontrado em {zip_path}")
            shp_path = os.path.join(tmp, shp_files[0])
            gdf = gpd.read_file(shp_path)

    name_col = _detect_name_column(gdf)
    print(f"  Coluna de nome detectada: '{name_col}'")
    print(f"  Total de regiões no shapefile: {len(gdf)}")

    gdf = gdf.reset_index(drop=True)
    gdf['geometry'] = gdf.geometry.buffer(0)
    gdf['_name'] = gdf[name_col].astype(str).str.strip()

    # Detectar duplicatas de nome
    dup_names = gdf['_name'][gdf['_name'].duplicated()].unique()
    if len(dup_names) > 0:
        print(f"  Aviso: {len(dup_names)} nomes duplicados: {list(dup_names[:5])}")

    # Encontrar pares vizinhos com touches
    joined = gdf.sjoin(gdf, predicate='touches', how='inner')
    joined = joined[joined.index != joined['index_right']]

    # Se muitos isolados (> 30%), usar intersects com buffer micro para cobrir gaps de precisão
    unique_with_neighbor = joined.index.nunique()
    if unique_with_neighbor < len(gdf) * 0.7:
        print(f"  Muitos isolados via touches ({len(gdf) - unique_with_neighbor}/{len(gdf)}), "
              f"usando intersects com buffer 1e-6°")
        gdf_buf = gdf.copy()
        gdf_buf['geometry'] = gdf_buf.geometry.buffer(1e-6)
        joined = gdf_buf.sjoin(gdf_buf, predicate='intersects', how='inner')
        joined = joined[joined.index != joined['index_right']]

    neighbors: dict[str, set] = {name: set() for name in gdf['_name']}

    for left_idx, row in joined.iterrows():
        right_idx = int(row['index_right'])
        name_a = gdf.loc[left_idx, '_name']
        name_b = gdf.loc[right_idx, '_name']
        if name_a != name_b:
            neighbors[name_a].add(name_b)
            neighbors[name_b].add(name_a)

    # Converter sets para listas ordenadas
    neighbors_sorted = {k: sorted(list(v)) for k, v in neighbors.items()}

    # Calcular estatísticas
    neighbor_counts = [len(v) for v in neighbors_sorted.values()]
    total_regions = len(neighbors_sorted)
    total_pairs = sum(neighbor_counts) // 2
    avg = sum(neighbor_counts) / total_regions if total_regions > 0 else 0
    max_count = max(neighbor_counts) if neighbor_counts else 0
    min_count = min(neighbor_counts) if neighbor_counts else 0
    most = max(neighbors_sorted, key=lambda k: len(neighbors_sorted[k])) if neighbors_sorted else ''
    least = min(neighbors_sorted, key=lambda k: len(neighbors_sorted[k])) if neighbors_sorted else ''
    isolated = sum(1 for c in neighbor_counts if c == 0)

    stats = {
        'shapefile': os.path.basename(zip_path),
        'name_column': name_col,
        'total_regions': total_regions,
        'total_neighbor_pairs': total_pairs,
        'avg_neighbors': round(avg, 4),
        'max_neighbors': max_count,
        'min_neighbors': min_count,
        'isolated_regions': isolated,
        'region_most_neighbors': most,
        'region_least_neighbors': least,
    }

    return {'neighbors': neighbors_sorted, 'stats': stats}


def main():
    parser = argparse.ArgumentParser(
        description='Gera JSON de vizinhança de bairros a partir de shapefile de cidade'
    )
    parser.add_argument(
        '--shapefile-zip',
        required=True,
        help='Caminho para o zip do shapefile de bairros'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Caminho do JSON de saída'
    )
    args = parser.parse_args()

    print(f"Lendo shapefile: {args.shapefile_zip}")
    result = build_neighborhood_neighbors(args.shapefile_zip)

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    stats = result['stats']
    print(f"OK: {stats['total_regions']} bairros, {stats['total_neighbor_pairs']} pares vizinhos")
    print(f"Avg vizinhos: {stats['avg_neighbors']}, isolados: {stats['isolated_regions']}")
    print(f"Salvo em: {args.output}")


if __name__ == '__main__':
    main()
