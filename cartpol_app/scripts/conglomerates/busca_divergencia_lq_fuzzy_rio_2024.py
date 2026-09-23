"""
Procura candidatos (>= MIN_VOTOS) onde o resultado do NOSSO algoritmo (fuzzy)
diverge visivelmente do LQ da literatura — para a comparação do TCC.

Roda a análise completa e imprime, por candidato concentrado:
  fuzzy (nosso veredito) x LQ_max x nº bairros LQ>1 (dispersão do sinal de LQ).
"""
from __future__ import annotations
import os
import pandas as pd
import batch_rio_vereadores_2024_csv as P

ULTRA_CSV = os.path.join(P.OUT_DIR, "rio_vereadores_2024_ultra_concentradores.csv")
MIN_VOTOS = 1000
MIN_TOPSHARE = 0.55


def main():
    dfu = pd.read_csv(ULTRA_CSV)
    cand = dfu[(dfu["total_votos"] >= MIN_VOTOS) & (dfu["top_share"] >= MIN_TOPSHARE)].copy()
    nrs = [str(int(x)) for x in cand["nr"]]
    print(f"Candidatos com >= {MIN_VOTOS} votos e top_share >= {MIN_TOPSHARE}: {len(nrs)}")

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
    eleitos = {e["nr"] for e in P.load_eleitos()}

    rows = []
    for nr in nrs:
        vd = votes_by_cand.get(nr)
        tot = total_by_cand.get(nr, 0)
        res = P.analyze_candidate(nr, vd, total_by_neigh, tot, total_place_votes,
                                  total_neighborhoods, qe, neighbors, display, sf)
        top = res["conglomerates"][0] if res["conglomerates"] else {}
        lqs = res["lq_hc_summary"]
        rows.append({
            "nome": name_by_cand.get(nr, nr),
            "nr": nr,
            "eleito": nr in eleitos,
            "votos": tot,
            "bairro_top": display.get(max(vd, key=vd.get), ""),
            "top_share": round(max(vd.values()) / tot, 3) if tot else 0,
            "bairros_filtrados": res["neighborhoods_after_filter"],
            "n_cong": res["total_conglomerates"],
            "RUESP_CAN_top": round(top.get("ruesp_can", 0), 3),
            "fuzzy": res["concentracao_final"],
            "interpret": res["interpretation"],
            "LQ_max": lqs.get("lq_max"),
            "bairro_LQ_max": lqs.get("bairro_lq_max"),
            "bairros_LQ>1": lqs.get("bairros_lq_acima_1"),
        })

    df = pd.DataFrame(rows)
    # foco: nosso veredito alto (concentrado) + LQ espalhado (muitos bairros LQ>1) => divergência visível
    df["div_score"] = df["fuzzy"] * df["bairros_LQ>1"].fillna(0)
    pd.set_option("display.width", 240); pd.set_option("display.max_rows", 80); pd.set_option("display.max_columns", 20)

    print("\n== CONCENTRADOS PELO NOSSO (fuzzy>=0.75) ORDENADOS POR DISPERSÃO DO LQ (bairros LQ>1) ==")
    a = df[df["fuzzy"] >= 0.75].sort_values(["bairros_LQ>1", "votos"], ascending=False)
    print(a[["nome", "eleito", "votos", "bairro_top", "top_share", "bairros_filtrados",
             "RUESP_CAN_top", "fuzzy", "interpret", "LQ_max", "bairros_LQ>1"]].to_string(index=False))

    out = os.path.join(P.OUT_DIR, "rio_divergencia_lq_fuzzy.csv")
    df.sort_values("fuzzy", ascending=False).to_csv(out, index=False)
    print(f"\nCSV completo: {out}")


if __name__ == "__main__":
    main()
