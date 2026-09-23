"""
Gera a vizinhança entre bairros (grafo) para cada município do RJ que possui
arquivo de mapa (zip) em `cartpol-pwa/src/assets/maps/county/`.

O resultado é um JSON por município, no formato compatível com
`politics_analysis.py` (chave `neighbors`), salvo em:
  cartpol_app/scripts/conglomerates/neighborhoods/rj/

E um índice com estatísticas em:
  cartpol_app/scripts/conglomerates/neighborhoods/rj/index.json

Uso:
    cd /home/iuri/TCC/cartpol && .venv/bin/python \
      cartpol_app/scripts/conglomerates/neighborhoods/batch_build_rj_neighborhood_neighbors.py
"""

from __future__ import annotations

import json
import os
import sys
import importlib.util
from dataclasses import dataclass
from typing import Dict, List

# Garantir imports locais do projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))  # raiz do repo
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

_CONG_DIR = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), ".."
))
_CONG_DIV_PATH = os.path.join(_CONG_DIR, "conglomerate_division.py")
_spec = importlib.util.spec_from_file_location(
    "conglomerate_division", _CONG_DIV_PATH
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
analyze_shapefile_conglomerates = _mod.analyze_shapefile_conglomerates


@dataclass(frozen=True)
class CountyZip:
    county_name: str
    filename: str


RJ_ZIPS: List[CountyZip] = [
    CountyZip("Angra dos Reis", "Angra dos Reis.zip"),
    CountyZip("Barra do Piraí", "Barra do Piraí.zip"),
    CountyZip("Barra Mansa", "Barra Mansa.zip"),
    CountyZip("Belford Roxo", "Belford Roxo.zip"),
    CountyZip("Bom Jesus do Itabapoana", "Bom Jesus do Itabapoana.zip"),
    CountyZip("Campos dos Goytacazes", "Campos dos Goytacazes.zip"),
    CountyZip("Duque de Caxias", "Duque de Caxias.zip"),
    CountyZip("Iguaba Grande", "Iguaba Grande.zip"),
    CountyZip("Itaboraí", "Itaboraí.zip"),
    CountyZip("Japeri", "Japeri.zip"),
    CountyZip("Macaé", "Macaé.zip"),
    CountyZip("Nilópolis", "Nilópolis.zip"),
    CountyZip("Niterói", "Niterói.zip"),
    CountyZip("Nova Iguaçu", "Nova Iguaçu.zip"),
    CountyZip("Quatis", "Quatis.zip"),
    CountyZip("Resende", "Resende.zip"),
    CountyZip("São Gonçalo", "São Gonçalo.zip"),
    CountyZip("São João de Meriti", "São João de Meriti.zip"),
    CountyZip("São Pedro da Aldeia", "São Pedro da Aldeia.zip"),
    CountyZip("Saquarema", "Saquarema.zip"),
    CountyZip("Tanguá", "Tanguá.zip"),
    CountyZip("Teresópolis", "Teresópolis.zip"),
]


def _repo_root() -> str:
    # /cartpol_app/scripts/conglomerates/neighborhoods -> root
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))


def _maps_county_dir() -> str:
    return os.path.normpath(
        os.path.join(_repo_root(), "..", "cartpol-pwa", "src", "assets", "maps", "county")
    )


def _out_dir() -> str:
    return os.path.normpath(os.path.join(_repo_root(), "cartpol_app", "scripts", "conglomerates", "neighborhoods", "rj"))


def _slug(name: str) -> str:
    # slug simples e estável para nomes em PT-BR
    import unicodedata

    s = unicodedata.normalize("NFD", name)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = s.lower()
    s = s.replace(" ", "_")
    s = s.replace("-", "_")
    return s


def main() -> None:
    maps_dir = _maps_county_dir()
    out_dir = _out_dir()
    os.makedirs(out_dir, exist_ok=True)

    index: Dict[str, object] = {
        "maps_dir": maps_dir,
        "output_dir": out_dir,
        "counties": [],
    }

    for item in RJ_ZIPS:
        zip_path = os.path.join(maps_dir, item.filename)
        if not os.path.exists(zip_path):
            print(f"[SKIP] zip não encontrado: {zip_path}")
            continue

        out_path = os.path.join(out_dir, f"neighbors_{_slug(item.county_name)}_bairros.json")
        print(f"[RUN] {item.county_name} -> {out_path}")

        neighbors, _conglomerates, stats = analyze_shapefile_conglomerates(
            zip_path,
            name_column=None,   # auto-detect (normalmente NM_BAIRRO)
            method="touches",
            output_json=None,   # vamos controlar o JSON aqui para ficar no padrão esperado
        )

        payload = {
            "county": item.county_name,
            "source_zip": zip_path,
            "stats": stats,
            "neighbors": neighbors,
        }
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        index["counties"].append(
            {
                "county": item.county_name,
                "zip": zip_path,
                "output": out_path,
                "stats": stats,
            }
        )

    index_path = os.path.join(out_dir, "index.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f"[OK] índice salvo em: {index_path}")


if __name__ == "__main__":
    main()

