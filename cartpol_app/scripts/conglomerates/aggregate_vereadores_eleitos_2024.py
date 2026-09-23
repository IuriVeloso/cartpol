"""
Agrega todos os CSVs test_*_vereadores_eleitos_2024.csv da pasta results/
e gera vereadores_eleitos_rj_2024_por_municipio.csv com estatísticas por município.
"""

from __future__ import annotations

import glob
import os

import pandas as pd

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")

PIB_PER_CAPITA = {
    "ANGRA DOS REIS": 53262.0,
    "BARRA DO PIRAÍ": 26833.0,
    "BARRA MANSA": 34816.0,
    "BELFORD ROXO": 17156.0,
    "BOM JESUS DO ITABAPOANA": 24343.0,
    "CAMPOS DOS GOYTACAZES": 72243.0,
    "DUQUE DE CAXIAS": 57170.0,
    "IGUABA GRANDE": 21517.0,
    "ITABORAÍ": 23078.0,
    "JAPERI": 14395.0,
    "MACAÉ": 66684.0,
    "NILÓPOLIS": 18782.0,
    "NITERÓI": 128333.0,
    "NOVA IGUAÇU": 21559.0,
    "QUATIS": 20945.0,
    "RESENDE": 80712.0,
    "SÃO GONÇALO": 18504.0,
    "SÃO JOÃO DE MERITI": 18935.0,
    "SÃO PEDRO DA ALDEIA": 25509.0,
    "SAQUAREMA": 458767.0,
    "TANGUÁ": 19902.0,
    "TERESÓPOLIS": 31880.0,
}

IDH_M = {
    "ANGRA DOS REIS": 0.724,
    "BARRA DO PIRAÍ": 0.733,
    "BARRA MANSA": 0.729,
    "BELFORD ROXO": 0.684,
    "BOM JESUS DO ITABAPOANA": 0.732,
    "CAMPOS DOS GOYTACAZES": 0.716,
    "DUQUE DE CAXIAS": 0.711,
    "IGUABA GRANDE": 0.761,
    "ITABORAÍ": 0.693,
    "JAPERI": 0.659,
    "MACAÉ": 0.764,
    "NILÓPOLIS": 0.753,
    "NITERÓI": 0.837,
    "NOVA IGUAÇU": 0.713,
    "QUATIS": 0.690,
    "RESENDE": 0.768,
    "SÃO GONÇALO": 0.739,
    "SÃO JOÃO DE MERITI": 0.719,
    "SÃO PEDRO DA ALDEIA": 0.712,
    "SAQUAREMA": 0.709,
    "TANGUÁ": 0.654,
    "TERESÓPOLIS": 0.730,
}

ESCALAS = [
    "irrisoria", "muito_baixa", "baixa", "media_baixa",
    "media", "media_alta", "alta", "muito_alta", "altissima",
]
GENEROS = ["masculino", "feminino", "indefinido"]

pattern = os.path.join(RESULTS_DIR, "test_*_vereadores_eleitos_2024.csv")
files = sorted(glob.glob(pattern))

if not files:
    raise SystemExit(f"Nenhum CSV encontrado em: {pattern}")

frames = []
for f in files:
    df = pd.read_csv(f, encoding="utf-8-sig")
    if "no_matches" in df.columns or (len(df.columns) == 1 and df.columns[0] == "no_matches"):
        continue
    frames.append(df)

if not frames:
    raise SystemExit("Todos os CSVs estão vazios ou sem matches.")

data = pd.concat(frames, ignore_index=True)
data = data[data["unmatched_in_csv"] == False].copy()

# Coluna genero pode não existir em CSVs antigos (sem rerrodada)
if "genero" not in data.columns:
    data["genero"] = "indefinido"

rows = []
for municipio, grp in data.groupby("municipio"):
    conc = grp["concentracao_final"].dropna()
    votes = grp["total_votes"].dropna()
    congs = grp["total_conglomerates"].dropna()

    row: dict = {
        "municipio": municipio,
        "qe": grp["qe"].iloc[0],
        "pib_per_capita": PIB_PER_CAPITA.get(municipio),
        "idh_m": IDH_M.get(municipio),
        "qtd_eleitos_processados": len(grp),
        "concentracao_media": round(float(conc.mean()), 4) if len(conc) else None,
        "concentracao_mediana": round(float(conc.median()), 4) if len(conc) else None,
        "concentracao_min": round(float(conc.min()), 4) if len(conc) else None,
        "concentracao_max": round(float(conc.max()), 4) if len(conc) else None,
        "total_votes_soma": int(votes.sum()) if len(votes) else None,
        "total_votes_media": round(float(votes.mean()), 1) if len(votes) else None,
        "total_conglomerates_media": round(float(congs.mean()), 2) if len(congs) else None,
    }

    # Contagem por escala
    interp_counts = grp["interpretation"].value_counts().to_dict()
    for escala in ESCALAS:
        row[f"qtd_{escala}"] = interp_counts.get(escala, 0)

    # Contagem por escala × gênero
    for genero in GENEROS:
        sub = grp[grp["genero"] == genero]
        sub_counts = sub["interpretation"].value_counts().to_dict()
        for escala in ESCALAS:
            row[f"qtd_{escala}_{genero}"] = sub_counts.get(escala, 0)

    rows.append(row)

out_df = pd.DataFrame(rows)
out_path = os.path.join(RESULTS_DIR, "vereadores_eleitos_rj_2024_por_municipio.csv")
out_df.to_csv(out_path, index=False, encoding="utf-8-sig")

print(f"Municípios processados: {len(out_df)}")
print(f"CSV gerado: {out_path}")
print()
print(out_df.to_string(index=False))
