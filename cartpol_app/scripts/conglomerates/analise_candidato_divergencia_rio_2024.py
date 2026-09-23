"""
Detalha o resultado do algoritmo para candidato(s) específico(s) e gera seus mapas
(nosso RUESP_CAN/RCAN_UESP vs LQ/HC), destacando a divergência com o LQ.

Uso: python analise_candidato_divergencia_rio_2024.py [nr1 nr2 ...]
Default: 77088 (SERGIO ANTONIO PINTO DOS SANTOS - Tijuca)
"""
from __future__ import annotations
import csv
import json
import os
import sys

import geopandas as gpd
import pandas as pd

import batch_rio_vereadores_2024_csv as P
import gerar_mapas_rio_2024 as M

NRS = sys.argv[1:] or ["77088"]
BAIRRO_OUT = os.path.join(P.OUT_DIR, "rio_divergencia_bairros.csv")
MAPS_DIR = os.path.join(P.OUT_DIR, "maps_divergencia")


def main():
    os.makedirs(MAPS_DIR, exist_ok=True)
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

    bairro_rows, nomes = [], {}
    for nr in NRS:
        vd = votes_by_cand.get(nr)
        tot = total_by_cand.get(nr, 0)
        res = P.analyze_candidate(nr, vd, total_by_neigh, tot, total_place_votes,
                                  total_neighborhoods, qe, neighbors, display, sf)
        nome = name_by_cand.get(nr, nr)
        nomes[nr] = nome
        top = res["conglomerates"][0] if res["conglomerates"] else {}

        print("=" * 78)
        print(f"{nome}  (nº {nr})   {tot} votos")
        print(f"  bairros com voto={res['neighborhoods_with_votes']}  ->  após Filtro 1={res['neighborhoods_after_filter']}  (classe {res['classification']})")
        print(f"  conglomerados={res['total_conglomerates']}")
        print(f"  >> NOSSO RESULTADO: fuzzy={res['concentracao_final']}  ({res['interpretation'].upper()})")
        print(f"     maior cong.: tam={top.get('size')}  RUESP_CAN={top.get('ruesp_can'):.3f}  RCAN_UESP={top.get('rcan_uesp'):.4f}  bairros={top.get('neighborhoods')}")

        # bairros que passaram no filtro (o "reduto real" segundo nosso algoritmo)
        filtrados = set()
        for cg in res["conglomerates"]:
            filtrados.update(cg["neighborhoods"])

        print(f"\n  >> LITERATURA (LQ): {res['lq_hc_summary'].get('bairros_lq_acima_1')} bairros com LQ>1 (LQ_max={res['lq_hc_summary'].get('lq_max')} @ {res['lq_hc_summary'].get('bairro_lq_max')})")
        print("     bairros LQ>1 (voto do candidato no bairro | LQ) — * = passou no NOSSO filtro:")
        lq_gt1 = sorted([(b, v) for b, v in res["lq_hc"].items() if v["lq"] > 1],
                        key=lambda kv: kv[1]["lq"], reverse=True)
        # mapear voto por bairro (display) para mostrar quão poucos votos geram LQ>1
        votos_disp = {display.get(bn, bn): v for bn, v in vd.items()}
        for b, v in lq_gt1:
            star = "*" if b in filtrados else " "
            print(f"       {star} {b:24s} votos={votos_disp.get(b, 0):5d}   LQ={v['lq']:8.2f}   HC={v['hc']:9.2f}")

        with open(os.path.join(P.JSON_DIR, f"{nr}_{P.slugify(nome)}.json"), "w", encoding="utf-8") as f:
            json.dump({"candidato": {"nr": nr, "nome": nome}, "qe": qe, **res}, f, ensure_ascii=False, indent=2)

        for bn, v_im in vd.items():
            v_m = total_by_neigh.get(bn, 0)
            lh = res["lq_hc"].get(display.get(bn, bn), {})
            bairro_rows.append({
                "nome_candidato": nome, "numero_candidato": nr, "bairro": display.get(bn, bn),
                "municipio_id": P.MUNICIPIO_ID, "municipio": "Rio de Janeiro", "UF": P.UF,
                "votos_absolutos_bairro": v_im, "votos_totais_bairro": v_m,
                "votos_totais_candidato": tot, "TOTAL_VOTOS_MUNICIPIO": total_place_votes,
                "RUESP(%)": round(v_m * 100 / total_place_votes, 6) if total_place_votes else 0,
                "RCAN_UESP(%)": round(v_im * 100 / v_m, 6) if v_m else 0,
                "RUESP_CAN(%)": round(v_im * 100 / tot, 6) if tot else 0,
                "LQ": lh.get("lq"), "HC": lh.get("hc"), "CI": lh.get("ci"),
            })

    with open(BAIRRO_OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(bairro_rows[0].keys()))
        w.writeheader(); w.writerows(bairro_rows)

    print("\nGerando mapas...")
    gdf = gpd.read_file(M.SHAPE_URI)
    gdf["bnorm"] = gdf[M.BAIRRO_COL].map(M.norm)
    dfb = pd.DataFrame(bairro_rows); dfb["bnorm"] = dfb["bairro"].map(M.norm)
    for nr in NRS:
        sub = dfb[dfb["numero_candidato"] == nr]
        merged = gdf.merge(sub, on="bnorm", how="left")
        for col, rotulo, cmap, sufixo in M.INDICADORES:
            out = os.path.join(MAPS_DIR, f"mapa_{M.slug(rotulo.split()[0])}_{M.slug(nomes[nr])}_{M.ANO}.png")
            M.mapa_individual(merged, col, rotulo, cmap, sufixo, nomes[nr], out)
    print(f"Mapas em: {MAPS_DIR}/")


if __name__ == "__main__":
    main()
