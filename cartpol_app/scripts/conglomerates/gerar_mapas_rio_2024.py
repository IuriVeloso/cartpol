"""
Gera mapas temáticos por bairro (município do Rio de Janeiro, Vereador 2024) a
partir de results_csv/rio_vereadores_2024_bairros.csv.

Para cada candidato selecionado: 4 mapas -> RCAN_UESP(%), RUESP_CAN(%), LQ, HC.
Opcionalmente: 1 mapa comparativo (vencedor por bairro em RCAN_UESP entre os
candidatos selecionados).

Usa o shapefile de bairros de Rio da pasta irmã cartpol-pwa (coluna NM_BAIRRO).
"""

from __future__ import annotations

import os
import unicodedata

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
CONG_DIR = os.path.join(BASE_DIR, "cartpol_app", "scripts", "conglomerates")

SHAPE_ZIP = "/home/iuri/TCC/cartpol-pwa/src/assets/maps/county/Rio de Janeiro.zip"
SHAPE_URI = f"zip://{SHAPE_ZIP}!Rio de Janeiro/Rio de Janeiro.shp"
BAIRRO_COL = "NM_BAIRRO"

BAIRROS_CSV = os.path.join(CONG_DIR, "results_csv", "rio_vereadores_2024_bairros.csv")
OUT_DIR = os.path.join(CONG_DIR, "results_csv", "maps")
ANO = 2024

CANDIDATOS = ["RODRIGO VIZEU", "ZICO", "CARLOS BOLSONARO", "MARCELO DINIZ"]
COMPARATIVO = True

# (coluna no CSV, rótulo, colormap, sufixo legenda)
INDICADORES = [
    ("RCAN_UESP(%)", "RCAN_UESP", "YlOrRd", "(%)"),
    ("RUESP_CAN(%)", "RUESP_CAN", "YlOrRd", "(%)"),
    ("LQ", "LQ (Location Quotient)", "RdYlGn", ""),
    ("HC", "HC (Hoover)", "RdBu", ""),
]

CORES_COMP = {
    CANDIDATOS[0]: "#1f77b4",
    CANDIDATOS[1]: "#ff7f0e",
    CANDIDATOS[2]: "#2ca02c",
    CANDIDATOS[3]: "#d62728",
}


def norm(s):
    if pd.isna(s):
        return ""
    s = str(s).strip().upper()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return "".join(c for c in s if c.isalnum())


def slug(s):
    return "".join(c if c.isalnum() else "_" for c in norm(s)).strip("_") or "x"


def mapa_individual(gdf, col, rotulo, cmap, sufixo, candidato, out_path):
    g = gdf.copy()
    g["val"] = pd.to_numeric(g[col], errors="coerce")
    _, ax = plt.subplots(1, 1, figsize=(12, 10))
    semdados = g[g["val"].isna()]
    if not semdados.empty:
        semdados.plot(ax=ax, color="lightgray", edgecolor="white", linewidth=0.4)
    comdados = g[g["val"].notna()]
    if not comdados.empty:
        comdados.plot(ax=ax, column="val", cmap=cmap, edgecolor="white", linewidth=0.4,
                      legend=True, legend_kwds={"label": f"{rotulo} {sufixo}".strip(),
                                                "orientation": "horizontal", "pad": 0.02, "shrink": 0.8})
    ax.set_title(f"{rotulo} — {candidato}\nBairros do Rio de Janeiro — {ANO}",
                 fontsize=14, fontweight="bold", pad=16)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"   {os.path.basename(out_path)}  ({comdados['val'].notna().sum()} bairros)")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print("Carregando shapefile...")
    gdf = gpd.read_file(SHAPE_URI)
    gdf["bnorm"] = gdf[BAIRRO_COL].map(norm)
    print(f"  bairros no mapa: {len(gdf)}")

    df = pd.read_csv(BAIRROS_CSV)
    df["bnorm"] = df["bairro"].map(norm)

    for cand in CANDIDATOS:
        sub = df[df["nome_candidato"] == cand]
        if sub.empty:
            print(f"[AVISO] sem linhas para {cand}")
            continue
        cobertura = gdf["bnorm"].isin(set(sub["bnorm"])).sum()
        print(f"\n{cand}: {len(sub)} bairros no CSV | casaram no mapa: {cobertura}")
        merged = gdf.merge(sub, on="bnorm", how="left")
        for col, rotulo, cmap, sufixo in INDICADORES:
            out = os.path.join(OUT_DIR, f"mapa_{slug(rotulo.split()[0])}_{slug(cand)}_{ANO}.png")
            mapa_individual(merged, col, rotulo, cmap, sufixo, cand, out)

    if COMPARATIVO:
        print("\nMapa comparativo (vencedor por bairro em RCAN_UESP)...")
        comp = df[df["nome_candidato"].isin(CANDIDATOS)].copy()
        comp["RCAN_UESP(%)"] = pd.to_numeric(comp["RCAN_UESP(%)"], errors="coerce")
        idx = comp.groupby("bnorm")["RCAN_UESP(%)"].idxmax().dropna()
        winners = comp.loc[idx, ["bnorm", "nome_candidato", "RCAN_UESP(%)"]]
        gwin = gdf.merge(winners, on="bnorm", how="left")
        gwin["cor"] = gwin["nome_candidato"].map(CORES_COMP)

        _, ax = plt.subplots(1, 1, figsize=(13, 11))
        gwin[gwin["cor"].isna()].plot(ax=ax, color="lightgray", edgecolor="white", linewidth=0.4)
        for cand in CANDIDATOS:
            sel = gwin[gwin["nome_candidato"] == cand]
            if not sel.empty:
                sel.plot(ax=ax, color=CORES_COMP[cand], edgecolor="white", linewidth=0.4)
        patches = [mpatches.Patch(color=CORES_COMP[c],
                                  label=f"{c} ({(gwin['nome_candidato'] == c).sum()} bairros)")
                   for c in CANDIDATOS]
        ax.legend(handles=patches, loc="upper left", bbox_to_anchor=(1.01, 1), fontsize=10, frameon=True)
        ax.set_title(f"Comparativo — vencedor por bairro (RCAN_UESP)\nRio de Janeiro — {ANO}",
                     fontsize=15, fontweight="bold", pad=16)
        ax.axis("off")
        plt.tight_layout()
        out = os.path.join(OUT_DIR, f"mapa_comparativo_rcan_uesp_{ANO}.png")
        plt.savefig(out, dpi=200, bbox_inches="tight")
        plt.close()
        print(f"   {os.path.basename(out)}")

    print(f"\nMapas em: {OUT_DIR}/")


if __name__ == "__main__":
    main()
