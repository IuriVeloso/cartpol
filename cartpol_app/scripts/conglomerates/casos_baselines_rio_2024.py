"""
Estudos de caso por baseline (Rio 2024, vereador): nosso índice fuzzy × LQ,
× HC, × LISA — um candidato-caso dedicado a cada método da literatura, escolhido
para evidenciar a limitação daquele baseline, + caso-controle de convergência.

Casos:
  × LQ   : CARLO CAIADO (55622, 47k votos)  [reforço: MARCIO RIBEIRO 55005, 57k]
  × HC   : MARCELO DINIZ (55888, 40k) vs PAULO ROBERTO (20623, 2.9k)
  × LISA : RAFAEL ALOISIO FREITAS (55123, 41k) vs PAULO ROBERTO (20623)
  controle: EMERSON DE SOUZA MELO (10394, 7.9k)

Saídas em results_csv/:
  caso_lq_carlo_caiado.csv / caso_hc_diniz_vs_paulo.csv / caso_lisa_rafael_vs_paulo.csv
  caso_controle_emerson.csv
  json/lisa_<nr>_<slug>.json (detalhe LISA por bairro)
  dotplot_concentracao_rio_2024.png (todos os candidatos, casos rotulados)
  casos_baselines_dados.json (números consolidados p/ o texto acadêmico)
"""

from __future__ import annotations

import csv
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import batch_rio_vereadores_2024_csv as P
import lisa_moran as L

CASOS = {
    "55622": "lq",        # Carlo Caiado
    "55005": "lq_ref",    # Marcio Ribeiro (reforço)
    "55888": "hc",        # Marcelo Diniz
    "20623": "ultra",     # Paulo Roberto (contraste HC e LISA)
    "55123": "lisa",      # Rafael Aloisio Freitas
    "10394": "controle",  # Emerson de Souza Melo
}

OUT = P.OUT_DIR
DOTPLOT = os.path.join(OUT, "dotplot_concentracao_rio_2024.png")
DADOS_JSON = os.path.join(OUT, "casos_baselines_dados.json")

FAIXAS = ["irrisoria", "muito_baixa", "baixa", "media_baixa", "media",
          "media_alta", "alta", "muito_alta"]  # limites reais: 0.125 em 0.125 (altissima = 1.0)

# Nome de urna reconhecível p/ rótulo do dot plot
URNA = {
    "55622": "CARLO CAIADO",
    "55005": "MARCIO RIBEIRO",
    "55888": "MARCELO DINIZ",
    "20623": "PAULO ROBERTO",
    "55123": "RAFAEL A. FREITAS",
    "10394": "EMERSON MELO",
}
# offset horizontal do rótulo (evita colisão) e posição vertical (cima/baixo)
LABEL_POS = {
    "55888": (-0.030, "baixo"),
    "55123": (0.000, "cima"),
    "55622": (0.030, "baixo"),
    "55005": (0.000, "baixo"),
    "10394": (-0.025, "cima"),
    "20623": (0.030, "cima"),
}


def analisar_caso(nr, votes_by_cand, total_by_neigh, total_by_cand, name_by_cand,
                  total_place, total_neighborhoods, qe, neighbors, display, sf):
    """Nosso resultado + LQ/HC/CI + LISA para um candidato. Chaves em display-name."""
    vd = votes_by_cand[nr]
    tot = total_by_cand[nr]
    res = P.analyze_candidate(nr, vd, total_by_neigh, tot, total_place,
                              total_neighborhoods, qe, neighbors, display, sf)

    votos_disp = {display.get(b, b): v for b, v in vd.items()}
    top_disp = max(votos_disp, key=votos_disp.get)

    # LISA sobre votos absolutos, universo = grafo (norm-keys); reduto em norm-key
    top_norm = max(vd, key=vd.get)
    lisa = L.lisa_summary(vd, neighbors, top_norm)
    # traduz chaves para display
    lisa["reduto"] = display.get(lisa["reduto"], lisa["reduto"])
    lisa["maior_cluster_HH"] = [display.get(b, b) for b in lisa["maior_cluster_HH"]]
    lisa["by_bairro"] = {display.get(b, b): v for b, v in lisa["by_bairro"].items()}

    lqhc = res["lq_hc"]  # display-key -> {lq, hc, ci}
    lq_sorted = sorted(lqhc.items(), key=lambda kv: kv[1]["lq"], reverse=True)
    hc_sorted = sorted(lqhc.items(), key=lambda kv: kv[1]["hc"], reverse=True)

    top_cong = res["conglomerates"][0] if res["conglomerates"] else {}
    return {
        "nr": nr,
        "nome": name_by_cand.get(nr, nr),
        "total_votos": tot,
        "bairros_com_voto": res["neighborhoods_with_votes"],
        "bairros_filtrados": res["neighborhoods_after_filter"],
        "fuzzy": res["concentracao_final"],
        "interpretacao": res["interpretation"],
        "n_conglomerados": res["total_conglomerates"],
        "conglomerados": res["conglomerates"],
        "top_cong": top_cong,
        "bairro_top": top_disp,
        "votos_bairro_top": votos_disp[top_disp],
        "votos_por_bairro": votos_disp,
        "lq_top10": [(b, v["lq"], votos_disp.get(b, 0)) for b, v in lq_sorted[:10]],
        "n_lq_acima_1": sum(1 for v in lqhc.values() if v["lq"] > 1),
        "hc_top5": [(b, v["hc"], votos_disp.get(b, 0)) for b, v in hc_sorted[:5]],
        "hc_total_positivo": round(sum(v["hc"] for v in lqhc.values() if v["hc"] > 0), 2),
        "lisa": lisa,
    }


def salvar_caso_csv(path, rows, fieldnames):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"  {os.path.basename(path)}")


def linha_resumo(c):
    return {
        "candidato": c["nome"], "nr": c["nr"], "votos": c["total_votos"],
        "fuzzy": c["fuzzy"], "interpretacao": c["interpretacao"],
        "n_conglomerados": c["n_conglomerados"],
        "bairro_reduto": c["bairro_top"], "votos_reduto": c["votos_bairro_top"],
        "LQ_max": c["lq_top10"][0][1] if c["lq_top10"] else None,
        "bairro_LQ_max": c["lq_top10"][0][0] if c["lq_top10"] else None,
        "votos_no_bairro_LQ_max": c["lq_top10"][0][2] if c["lq_top10"] else None,
        "n_LQ_acima_1": c["n_lq_acima_1"],
        "HC_total_positivo": c["hc_total_positivo"],
        "moran_global": c["lisa"]["moran_global"],
        "moran_global_p": c["lisa"]["moran_global_p"],
        "n_HH_sig": c["lisa"]["n_HH_sig"],
        "reduto_quad_LISA": c["lisa"]["reduto_quad"],
        "reduto_p_LISA": c["lisa"]["reduto_p"],
    }


def dotplot(all_scores, eleitos_nrs, casos, path):
    """Strip plot 0-1 de todos os candidatos; eleitos destacados; casos rotulados."""
    rng = np.random.default_rng(7)
    xs = np.array([s for _, s in all_scores])
    nrs = [n for n, _ in all_scores]
    ys = rng.uniform(-0.35, 0.35, size=len(xs))

    is_eleito = np.array([n in eleitos_nrs for n in nrs])
    caso_nrs = {c["nr"]: c for c in casos}

    fig, ax = plt.subplots(figsize=(14, 5.5))
    # faixas reais da interpretação: cortes de 0.125 em 0.125
    lims = np.arange(0, 1.0001, 0.125)
    for i in range(8):
        ax.axvspan(lims[i], lims[i + 1], color=plt.cm.RdYlGn_r(i / 7), alpha=0.10)
        ax.text((lims[i] + lims[i + 1]) / 2, 0.68, FAIXAS[i].replace("_", "\n"),
                ha="center", va="top", fontsize=7.5, color="0.35")

    ax.scatter(xs[~is_eleito], ys[~is_eleito], s=14, alpha=0.35,
               color="0.55", label=f"não eleitos (n={int((~is_eleito).sum())})")
    ax.scatter(xs[is_eleito], ys[is_eleito], s=34, alpha=0.9, color="#1f77b4",
               edgecolor="white", linewidth=0.5, label=f"eleitos (n={int(is_eleito.sum())})")

    # rotular casos (nome de urna + offsets manuais anti-colisão)
    for i, n in enumerate(nrs):
        if n in caso_nrs:
            c = caso_nrs[n]
            label = f"{URNA.get(n, c['nome'].split()[0])}\n({c['fuzzy']:.2f})"
            dx, lado = LABEL_POS.get(n, (0.0, "baixo"))
            ty = 0.50 if lado == "cima" else -0.66
            ax.scatter([xs[i]], [ys[i]], s=90, facecolor="none",
                       edgecolor="crimson", linewidth=1.6, zorder=5)
            ax.annotate(label, (xs[i], ys[i]), xytext=(xs[i] + dx, ty),
                        fontsize=8, ha="center", color="crimson",
                        arrowprops=dict(arrowstyle="-", color="crimson", lw=0.8))

    ax.set_xlim(0, 1)
    ax.set_ylim(-0.85, 0.75)
    ax.set_yticks([])
    ax.set_xlabel("Concentração (índice fuzzy)")
    ax.set_title("Concentração eleitoral — vereadores do Rio de Janeiro, 2024\n"
                 "(todos os candidatos com perfil computável; casos de estudo destacados)",
                 fontsize=12, fontweight="bold")
    ax.legend(loc="upper right", fontsize=9, framealpha=0.9)
    plt.tight_layout()
    plt.savefig(path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"  {os.path.basename(path)}")


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(P.JSON_DIR, exist_ok=True)

    print("Carregando dados (1 passada no CSV grande)...")
    sec_map, display, total_neighborhoods = P.load_section_to_neighborhood()
    neighbors = P.load_neighbors_graph(display)
    votes_by_cand, total_by_neigh, total_by_cand, name_by_cand = P.aggregate_votes(sec_map)
    total_place = sum(total_by_neigh.values())
    qe = P.load_qe()
    sf = P.SistemaFuzzyMamdani(
        arq_variaveis=os.path.join(P.FUZZY_DIR, "variaveis-fuzzy.json"),
        arq_regras=os.path.join(P.FUZZY_DIR, "regras-fuzzy.json"),
        defuzz="centroide",
    )
    eleitos_nrs = {e["nr"] for e in P.load_eleitos()}

    # ---------- casos ----------
    print("\nAnalisando candidatos-caso (nosso + LQ/HC + LISA c/ permutação)...")
    casos = {}
    for nr in CASOS:
        c = analisar_caso(nr, votes_by_cand, total_by_neigh, total_by_cand,
                          name_by_cand, total_place, total_neighborhoods, qe,
                          neighbors, display, sf)
        casos[nr] = c
        lisa_out = os.path.join(P.JSON_DIR, f"lisa_{nr}_{P.slugify(c['nome'])}.json")
        with open(lisa_out, "w", encoding="utf-8") as f:
            json.dump(c["lisa"], f, ensure_ascii=False, indent=2)
        print(f"  {c['nome'][:30]:30s} fuzzy={c['fuzzy']:.4f} ({c['interpretacao']})  "
              f"MoranG={c['lisa']['moran_global']:.3f} (p={c['lisa']['moran_global_p']:.3f})  "
              f"reduto={c['bairro_top']} [{c['lisa']['reduto_quad']}]")

    # ---------- mini-tabelas por caso ----------
    print("\nSalvando mini-tabelas por caso...")
    campos = list(linha_resumo(casos["55622"]).keys())
    salvar_caso_csv(os.path.join(OUT, "caso_lq_carlo_caiado.csv"),
                    [linha_resumo(casos["55622"]), linha_resumo(casos["55005"])], campos)
    salvar_caso_csv(os.path.join(OUT, "caso_hc_diniz_vs_paulo.csv"),
                    [linha_resumo(casos["55888"]), linha_resumo(casos["20623"])], campos)
    salvar_caso_csv(os.path.join(OUT, "caso_lisa_rafael_vs_paulo.csv"),
                    [linha_resumo(casos["55123"]), linha_resumo(casos["20623"])], campos)
    salvar_caso_csv(os.path.join(OUT, "caso_controle_emerson.csv"),
                    [linha_resumo(casos["10394"])], campos)

    # ---------- dot plot: todos os candidatos ----------
    print("\nRodando fuzzy para todos os candidatos (dot plot)...")
    all_scores = []
    for nr, vd in votes_by_cand.items():
        tot = total_by_cand.get(nr, 0)
        if tot <= 0:
            continue
        res = P.analyze_candidate(nr, vd, total_by_neigh, tot, total_place,
                                  total_neighborhoods, qe, neighbors, display, sf)
        if res["total_conglomerates"] > 0:
            all_scores.append((nr, res["concentracao_final"]))
    print(f"  candidatos com perfil computável: {len(all_scores)}")
    # persistir p/ replots rápidos sem re-rodar o pipeline
    with open(os.path.join(OUT, "dotplot_scores.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["nr", "fuzzy", "eleito"])
        for n, s in all_scores:
            w.writerow([n, s, n in eleitos_nrs])
    dotplot(all_scores, eleitos_nrs, list(casos.values()), DOTPLOT)

    # ---------- consolidado p/ texto ----------
    consolidado = {nr: {k: v for k, v in c.items() if k not in ("votos_por_bairro",)}
                   for nr, c in casos.items()}
    for nr, c in consolidado.items():
        c["lisa"] = {k: v for k, v in c["lisa"].items() if k != "by_bairro"}
    consolidado["_meta"] = {
        "qe": qe, "total_votos_municipio": total_place,
        "total_bairros": total_neighborhoods,
        "n_candidatos_dotplot": len(all_scores),
        "limiar_filtro1": round(qe * P.THRESHOLD_PERCENT / total_neighborhoods, 2),
    }
    with open(DADOS_JSON, "w", encoding="utf-8") as f:
        json.dump(consolidado, f, ensure_ascii=False, indent=2)
    print(f"\nConsolidado: {DADOS_JSON}")


if __name__ == "__main__":
    main()
