"""
Gera JSON de vizinhança entre municípios a partir do shapefile IBGE (zip).

As chaves do JSON são os IDs do modelo `County` no Django (como em
`neighborhood__county_id`). O shapefile usa CD_MUN (IBGE); em muitos bancos
`County.tse_id` não coincide com o IBGE — por isso o casamento é feito pelo
nome do município (normalização + rapidfuzz), com score mínimo configurável.

Uso:
    python build_county_neighbors_from_shapefile.py --uf RJ --output neighbors_rj_municipios.json
"""

import argparse
import json
import os
import sys
import tempfile
import unicodedata
import zipfile
from typing import Dict, List, Set, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cartpol.settings')

import django

django.setup()

import geopandas as gpd
from rapidfuzz import fuzz, process

from cartpol_app.models import County, State


def _default_maps_state_dir() -> str:
    return os.path.normpath(
        os.path.join(
            BASE_DIR, '..', 'cartpol-pwa', 'src', 'assets', 'maps', 'state'
        )
    )


def _normalize_name(s: str) -> str:
    s = str(s).upper().strip()
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return ' '.join(s.split())


def _find_state_shapefile_zip(maps_state_dir: str, uf: str) -> str:
    uf = uf.upper()
    candidates = sorted(
        f for f in os.listdir(maps_state_dir)
        if f.upper().startswith(f'{uf}_MUNICIPIOS_') and f.lower().endswith('.zip')
    )
    if not candidates:
        raise FileNotFoundError(
            f'Nenhum zip de municípios para UF={uf} em {maps_state_dir}'
        )
    return os.path.join(maps_state_dir, candidates[-1])


def _read_municipalities_gdf(zip_path: str) -> gpd.GeoDataFrame:
    with zipfile.ZipFile(zip_path) as zf:
        with tempfile.TemporaryDirectory() as tmp:
            zf.extractall(tmp)
            shp_name = next(
                n for n in zf.namelist() if n.lower().endswith('.shp'))
            stem = os.path.join(tmp, shp_name[:-4])
            gdf = gpd.read_file(stem + '.shp')
    if 'CD_MUN' not in gdf.columns or 'NM_MUN' not in gdf.columns:
        raise ValueError(
            f'Shapefile sem CD_MUN/NM_MUN: {zip_path} colunas={list(gdf.columns)}'
        )
    gdf = gdf.reset_index(drop=True)
    gdf['geometry'] = gdf.geometry.buffer(0)
    gdf['CD_MUN'] = gdf['CD_MUN'].astype(int)
    return gdf


def _touching_pairs_ibge(gdf: gpd.GeoDataFrame) -> Set[Tuple[int, int]]:
    joined = gdf.sjoin(gdf, predicate='touches', how='inner')
    joined = joined[joined.index != joined['index_right']]
    pairs: Set[Tuple[int, int]] = set()
    for left_idx, row in joined.iterrows():
        right_idx = int(row['index_right'])
        i, j = int(left_idx), right_idx
        if i > j:
            i, j = j, i
        a = int(gdf.loc[i, 'CD_MUN'])
        b = int(gdf.loc[j, 'CD_MUN'])
        if a > b:
            a, b = b, a
        pairs.add((a, b))
    return pairs


def _map_ibge_to_county_pk(
    gdf: gpd.GeoDataFrame,
    state: State,
    min_score: float,
) -> Tuple[Dict[int, int], List[Tuple[int, str]]]:
    counties = list(
        County.objects.filter(state=state).values_list('id', 'name', 'tse_id')
    )
    by_norm: Dict[str, int] = {}
    for pk, name, _tse in counties:
        key = _normalize_name(name)
        if key not in by_norm:
            by_norm[key] = pk

    name_list = [c[1] for c in counties]
    norm_list = [_normalize_name(n) for n in name_list]

    ibge_to_pk: Dict[int, int] = {}
    failures: List[Tuple[int, str]] = []

    for _, row in gdf.iterrows():
        ibge = int(row['CD_MUN'])
        nm_shp = _normalize_name(str(row['NM_MUN']))
        pk = by_norm.get(nm_shp)
        if pk is None:
            hit = process.extractOne(
                nm_shp,
                norm_list,
                scorer=fuzz.token_sort_ratio,
            )
            if hit is None or hit[1] < min_score:
                failures.append((ibge, str(row['NM_MUN'])))
                continue
            idx = hit[2]
            pk = counties[idx][0]
        ibge_to_pk[ibge] = pk

    return ibge_to_pk, failures


def build_neighbors_for_uf(
    uf: str,
    maps_state_dir: str,
    min_score: float = 90.0,
) -> Tuple[Dict[str, List[str]], Dict[str, int]]:
    zip_path = _find_state_shapefile_zip(maps_state_dir, uf)
    gdf = _read_municipalities_gdf(zip_path)
    pairs = _touching_pairs_ibge(gdf)

    ibge_neighbors: Dict[int, Set[int]] = {}
    for a, b in pairs:
        ibge_neighbors.setdefault(a, set()).add(b)
        ibge_neighbors.setdefault(b, set()).add(a)

    state = State.objects.get(name=uf.upper())
    ibge_to_pk, failures = _map_ibge_to_county_pk(gdf, state, min_score=min_score)

    pk_neighbors: Dict[int, Set[int]] = {}
    for ibge_a, ibge_b in pairs:
        pka = ibge_to_pk.get(ibge_a)
        pkb = ibge_to_pk.get(ibge_b)
        if pka is None or pkb is None:
            continue
        pk_neighbors.setdefault(pka, set()).add(pkb)
        pk_neighbors.setdefault(pkb, set()).add(pka)

    out: Dict[str, List[str]] = {}
    for pk, _, _ in County.objects.filter(state=state).values_list('id', 'name', 'tse_id'):
        nbrs = sorted(str(x) for x in pk_neighbors.get(pk, set()))
        out[str(pk)] = nbrs

    stats = {
        'shapefile_municipios': len(gdf),
        'ibge_mapeados': len(ibge_to_pk),
        'falhas_nome': len(failures),
        'zip_usado': zip_path,
    }
    return out, stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Gera neighbors.json entre municípios (IDs County) a partir do shapefile UF'
    )
    parser.add_argument('--uf', required=True, help='Sigla da UF (ex.: RJ)')
    parser.add_argument(
        '--maps-state-dir',
        default=_default_maps_state_dir(),
        help='Pasta com zips UF_*_Municipios_*.zip',
    )
    parser.add_argument('--output', required=True, help='JSON de saída')
    parser.add_argument(
        '--min-score',
        type=float,
        default=90.0,
        help='Score mínimo rapidfuzz (0-100) para casar nome shapefile vs County',
    )
    args = parser.parse_args()

    neighbors, stats = build_neighbors_for_uf(
        args.uf, args.maps_state_dir, min_score=args.min_score
    )
    payload = {'neighbors': neighbors, 'stats': stats}
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(
        f"OK: {len(neighbors)} municípios; mapeados IBGE→County: {stats['ibge_mapeados']}/"
        f"{stats['shapefile_municipios']}; falhas nome: {stats['falhas_nome']}"
    )
    print(f"Salvo em: {args.output}")


if __name__ == '__main__':
    main()
