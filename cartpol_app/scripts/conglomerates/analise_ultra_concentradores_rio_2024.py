"""
Varre TODOS os candidatos a vereador do Rio (2024) e rankeia por concentração
num único bairro (ultra-concentradores), reutilizando a agregação CSV-only.

Para cada candidato:
  top_share = votos no bairro mais votado / votos totais do candidato  (= RUESP_CAN de 1 bairro)
  hhi       = índice Herfindahl (soma dos quadrados das participações por bairro)
Saída: results_csv/rio_vereadores_2024_ultra_concentradores.csv
"""
from __future__ import annotations

import csv
import os

import batch_rio_vereadores_2024_csv as P  # mesma pasta

OUT = os.path.join(P.OUT_DIR, "rio_vereadores_2024_ultra_concentradores.csv")


def main():
    os.makedirs(P.OUT_DIR, exist_ok=True)
    print("Mapa seção->bairro...")
    sec_map, display, _ = P.load_section_to_neighborhood()
    print("Agregando votos de TODOS os candidatos (Rio, Vereador)...")
    votes_by_cand, total_by_neigh, total_by_cand, name_by_cand = P.aggregate_votes(sec_map)

    eleitos = {e["nr"]: e for e in P.load_eleitos()}
    print(f"candidatos: {len(votes_by_cand)} | eleitos: {len(eleitos)}")

    rows = []
    for nr, bairros in votes_by_cand.items():
        tot = total_by_cand.get(nr, 0)
        if tot <= 0:
            continue
        top_b, top_v = max(bairros.items(), key=lambda kv: kv[1])
        top_share = top_v / tot
        hhi = sum((v / tot) ** 2 for v in bairros.values())
        e = eleitos.get(nr)
        rows.append({
            "nr": nr,
            "nome": name_by_cand.get(nr, ""),
            "eleito": bool(e),
            "partido": e["partido"] if e else "",
            "total_votos": tot,
            "n_bairros_com_voto": len(bairros),
            "bairro_top": display.get(top_b, top_b),
            "votos_bairro_top": top_v,
            "top_share": round(top_share, 4),
            "hhi": round(hhi, 4),
        })

    # ordenar por concentração e, entre iguais, por votação total (mais votos = mais notável)
    rows.sort(key=lambda r: (r["top_share"], r["total_votos"]), reverse=True)

    with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"OK -> {OUT}  ({len(rows)} candidatos)")

    # relatório rápido por faixas de votação
    def tier(rows, minv):
        sub = [r for r in rows if r["total_votos"] >= minv]
        sub.sort(key=lambda r: (r["top_share"], r["total_votos"]), reverse=True)
        return sub

    print("\n=== 100% num único bairro (top_share = 1.0) ===")
    puros = [r for r in rows if r["top_share"] >= 0.9999]
    print(f"total: {len(puros)} candidatos | máx votos entre eles: "
          f"{max((r['total_votos'] for r in puros), default=0)}")
    for r in sorted(puros, key=lambda r: r["total_votos"], reverse=True)[:8]:
        print(f"  {r['nome'][:34]:34s} {r['total_votos']:6d} votos  100% em {r['bairro_top']}"
              f"  {'[ELEITO]' if r['eleito'] else ''}")

    for mn, label in [(1000, ">=1000 votos"), (5000, ">=5000 votos")]:
        print(f"\n=== Mais concentrados com {label} ===")
        for r in tier(rows, mn)[:10]:
            print(f"  {r['nome'][:32]:32s} {r['total_votos']:6d}v  top_share={r['top_share']:.3f}"
                  f"  HHI={r['hhi']:.3f}  bairro={r['bairro_top']}  {'[ELEITO '+r['partido']+']' if r['eleito'] else ''}")


if __name__ == "__main__":
    main()
