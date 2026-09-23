"""
Roda a análise COMPLETA (conglomerados + fuzzy + LQ/HC/CI) nos ultra-concentradores
não-eleitos do Rio 2024 e gera seus mapas. Demonstra que o algoritmo marca esses
candidatos como concentração 'alta/muito_alta/altíssima'.

Reutiliza batch_rio_vereadores_2024_csv (agregação/análise) e gerar_mapas_rio_2024 (mapas).
"""
from __future__ import annotations

import csv
import json
import os

import geopandas as gpd
import pandas as pd

import batch_rio_vereadores_2024_csv as P
import gerar_mapas_rio_2024 as M

ULTRA_CSV = os.path.join(P.OUT_DIR, "rio_vereadores_2024_ultra_concentradores.csv")
BAIRRO_OUT = os.path.join(P.OUT_DIR, "rio_ultraconc_bairros.csv")
MAPS_DIR = os.path.join(P.OUT_DIR, "maps_ultra")
N_SEL = 4
MIN_VOTOS = 500


def main():
    os.makedirs(MAPS_DIR, exist_ok=True)

    # 1) selecionar candidatos-vitrine: não-eleitos, >= MIN_VOTOS, mais concentrados
    dfu = pd.read_csv(ULTRA_CSV)
    sel = (dfu[(~dfu["eleito"]) & (dfu["total_votos"] >= MIN_VOTOS)]
           .sort_values(["top_share", "total_votos"], ascending=False)
           .head(N_SEL))
    nrs = [str(int(x)) for x in sel["nr"]]
    print("Selecionados (ultra-concentradores):")
    for _, r in sel.iterrows():
        print(f"  {r['nome']}  {int(r['total_votos'])}v  top_share={r['top_share']:.3f}  bairro={r['bairro_top']}")

    # 2) agregação CSV-only + grafo + fuzzy
    print("\nAgregando votos...")
    sec_map, display, total_neighborhoods = P.load_section_to_neighborhood()
    neighbors = P.load_neighbors_graph(display)
    votes_by_cand, total_by_neigh, total_by_cand, name_by_cand = P.aggregate_votes(sec_map)
    total_place_votes = sum(total_by_neigh.values())
    qe = P.load_qe()
    sf = P.SistemaFuzzyMamdani(
        arq_variaveis=os.path.join(P.FUZZY_DIR, "variaveis-fuzzy.json"),
        arq_regras=os.path.join(P.FUZZY_DIR, "regras-fuzzy.json"),
        defuzz="centroide",
    )

    # 3) análise completa por candidato
    print("\n=== ANÁLISE FUZZY DOS ULTRA-CONCENTRADORES ===")
    bairro_rows = []
    nomes_map = {}
    for nr in nrs:
        vd = votes_by_cand.get(nr)
        tot = total_by_cand.get(nr, 0)
        res = P.analyze_candidate(nr, vd, total_by_neigh, tot, total_place_votes,
                                  total_neighborhoods, qe, neighbors, display, sf)
        nome = name_by_cand.get(nr, nr)
        nomes_map[nr] = nome
        top = res["conglomerates"][0] if res["conglomerates"] else {}
        lqs = res["lq_hc_summary"]
        print(f"\n▶ {nome} ({tot} votos)")
        print(f"    bairros filtrados={res['neighborhoods_after_filter']}  conglomerados={res['total_conglomerates']}")
        print(f"    FUZZY concentração = {res['concentracao_final']}  ({res['interpretation']})")
        print(f"    maior cong.: tam={top.get('size')}  RUESP_CAN={top.get('ruesp_can'):.3f}  "
              f"RCAN_UESP={top.get('rcan_uesp'):.4f}  fuzzy={top.get('fuzzy_concentration')}")
        print(f"    LQ_max={lqs.get('lq_max')} @ {lqs.get('bairro_lq_max')}  |  bairros LQ>1={lqs.get('bairros_lq_acima_1')}")

        with open(os.path.join(P.JSON_DIR, f"{nr}_{P.slugify(nome)}.json"), "w", encoding="utf-8") as f:
            json.dump({"candidato": {"nr": nr, "nome": nome}, "qe": qe, **res}, f, ensure_ascii=False, indent=2)

        for bnorm, v_im in vd.items():
            v_m = total_by_neigh.get(bnorm, 0)
            lh = res["lq_hc"].get(display.get(bnorm, bnorm), {})
            bairro_rows.append({
                "nome_candidato": nome,
                "numero_candidato": nr,
                "bairro": display.get(bnorm, bnorm),
                "municipio_id": P.MUNICIPIO_ID,
                "municipio": "Rio de Janeiro",
                "UF": P.UF,
                "votos_absolutos_bairro": v_im,
                "votos_totais_bairro": v_m,
                "votos_totais_candidato": tot,
                "TOTAL_VOTOS_MUNICIPIO": total_place_votes,
                "RUESP(%)": round(v_m * 100 / total_place_votes, 6) if total_place_votes else 0,
                "RCAN_UESP(%)": round(v_im * 100 / v_m, 6) if v_m else 0,
                "RUESP_CAN(%)": round(v_im * 100 / tot, 6) if tot else 0,
                "LQ": lh.get("lq"), "HC": lh.get("hc"), "CI": lh.get("ci"),
            })

    with open(BAIRRO_OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(bairro_rows[0].keys()))
        w.writeheader()
        w.writerows(bairro_rows)
    print(f"\nBairros CSV: {BAIRRO_OUT}")

    # 4) mapas (reusa mapa_individual do gerador)
    print("\nGerando mapas dos ultra-concentradores...")
    gdf = gpd.read_file(M.SHAPE_URI)
    gdf["bnorm"] = gdf[M.BAIRRO_COL].map(M.norm)
    dfb = pd.DataFrame(bairro_rows)
    dfb["bnorm"] = dfb["bairro"].map(M.norm)
    for nr in nrs:
        nome = nomes_map[nr]
        sub = dfb[dfb["numero_candidato"] == nr]
        merged = gdf.merge(sub, on="bnorm", how="left")
        for col, rotulo, cmap, sufixo in M.INDICADORES:
            out = os.path.join(MAPS_DIR, f"mapa_{M.slug(rotulo.split()[0])}_{M.slug(nome)}_{M.ANO}.png")
            M.mapa_individual(merged, col, rotulo, cmap, sufixo, nome, out)
    print(f"\nMapas em: {MAPS_DIR}/")


if __name__ == "__main__":
    main()
