"""
Pipeline CSV-only (sem banco Django) de concentração política por bairros para
os VEREADORES ELEITOS de 2024 no município do Rio de Janeiro.

Substitui a leitura do banco (VotesInNeighborhood) por:
    votacao_secao_2024_RJ.csv  ⋈  RIOINT2024.csv
onde a chave é (municipio_id, NR_ZONA, NR_SECAO) -> name_neighborhood (bairro).

Reproduz EXATAMENTE a lógica de cartpol_app/scripts/conglomerates/politics_analysis.py
(filtros 1/2/3, detecção de conglomerados por vizinhança, indicadores RUESP/
RUESP_CAN/RCAN_UESP por conglomerado, e concentração fuzzy Mamdani), acrescentando
LQ, HC (Silva & Davidian) e CI (Carvalho) por bairro para a comparação do TCC.

Saídas (em cartpol_app/scripts/conglomerates/results_csv/):
  - rio_vereadores_2024_fuzzy_summary.csv   -> 1 linha por eleito (tabela comparativa)
  - rio_vereadores_2024_bairros.csv         -> indicadores por (candidato, bairro),
                                               compatível com candidates_vote_generate_maps.py
  - json/<nr>_<slug>.json                   -> detalhe completo por candidato
"""

from __future__ import annotations

import csv
import importlib.util
import json
import os
import sys
import unicodedata
from typing import Any, Dict, List, Set, Tuple

import pandas as pd

sys.setrecursionlimit(50000)

# ----------------------------------------------------------------------------
# Configuração (Rio de Janeiro capital, Vereador, 2024)
# ----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
CONG_DIR = os.path.join(BASE_DIR, "cartpol_app", "scripts", "conglomerates")

VOTES_CSV = os.path.join(BASE_DIR, "data", "votacao_secao_2024_RJ.csv")
RIOINT_CSV = os.path.join(BASE_DIR, "data", "RIOINT2024.csv")
NEIGHBORS_JSON = os.path.join(CONG_DIR, "neighborhoods", "neighbors_rio_de_janeiro_bairros.json")
ELEITOS_CSV = os.path.join(CONG_DIR, "votacao_candidato-municipio_vereador_2024_sudeste_rj_eleito.csv")
QE_CSV = os.path.join(CONG_DIR, "quociente_eleitoral-uf_vereador_2024_rj.csv")

MUNICIPIO_ID = "60011"
MUNICIPIO_NOME = "RIO DE JANEIRO"
UF = "RJ"
CD_CARGO = "13"          # Vereador
ANO = 2024
THRESHOLD_PERCENT = 0.05  # Filtro 1: > 5% do Q.E. / nº de bairros
CHUNK = 500_000

OUT_DIR = os.path.join(CONG_DIR, "results_csv")
JSON_DIR = os.path.join(OUT_DIR, "json")

# Sistema fuzzy (importado por caminho, sem tocar no Django)
FUZZY_DIR = os.path.join(BASE_DIR, "cartpol_app", "scripts", "fuzzy_logic")
_spec = importlib.util.spec_from_file_location("fuzzy_cartpol", os.path.join(FUZZY_DIR, "fuzzy_cartpol.py"))
_fuzzy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fuzzy)
SistemaFuzzyMamdani = _fuzzy.SistemaFuzzyMamdani


# ----------------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------------
def norm(s: Any) -> str:
    """Chave canônica de bairro (maiúsculas, sem acento, só alfanumérico)."""
    if s is None:
        return ""
    s = str(s).strip().upper()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return "".join(c for c in s if c.isalnum())


def slugify(s: str) -> str:
    s = str(s).strip().upper()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    out = "".join(c if c.isalnum() else "_" for c in s).lower()
    while "__" in out:
        out = out.replace("__", "_")
    return out.strip("_")


# ----------------------------------------------------------------------------
# Funções puras copiadas de politics_analysis.py (mesma lógica/resultados)
# ----------------------------------------------------------------------------
def calculate_lq_hc(votes_dict, total_votes_dict, total_political_votes, total_place_votes):
    """LQ e HC por bairro (Silva & Davidian, BPSR 2013) + CI (Carvalho)."""
    result: Dict[str, Dict[str, float]] = {}
    if total_political_votes == 0 or total_place_votes == 0:
        return result
    for neighborhood, v_im in votes_dict.items():
        v_m = total_votes_dict.get(neighborhood, 0)
        if v_m == 0:
            continue
        lq = (v_im / total_political_votes) / (v_m / total_place_votes)
        hc = (total_political_votes * v_m / total_place_votes) * (lq - 1)
        ci = (v_im / total_political_votes) * (v_m / total_place_votes)
        result[neighborhood] = {"lq": round(lq, 4), "hc": round(hc, 2), "ci": round(ci, 8)}
    return result


def filter_significant_votes(votes_dict, qe, total_neighborhoods, threshold_percent=0.05):
    """Filtro 1: mantém bairros com votos > threshold_percent * QE / nº bairros."""
    neighborhoods_denominator = max(int(total_neighborhoods or 0), 1)
    min_votes = (qe * threshold_percent) / neighborhoods_denominator
    return {n: v for n, v in votes_dict.items() if v > min_votes}


def classify_neighborhood_count(filtered_count, total_count):
    """Filtro 2: P (<20%), M (<=50%), G (>50%)."""
    if total_count == 0:
        return "P"
    p = filtered_count / total_count
    if p < 0.20:
        return "P"
    if p <= 0.50:
        return "M"
    return "G"


def find_filtered_conglomerates(filtered_neighborhoods: Set[str], neighbors: Dict[str, List[str]]):
    """Componentes conexos (DFS) dos bairros filtrados no grafo de vizinhança."""
    visited: Set[str] = set()
    conglomerates: List[Set[str]] = []

    def dfs(n: str, cluster: Set[str]):
        if n in visited or n not in filtered_neighborhoods:
            return
        visited.add(n)
        cluster.add(n)
        for nb in neighbors.get(n, []):
            if nb in filtered_neighborhoods and nb not in visited:
                dfs(nb, cluster)

    for n in filtered_neighborhoods:
        if n not in visited:
            cluster: Set[str] = set()
            dfs(n, cluster)
            if cluster:
                conglomerates.append(cluster)
    conglomerates.sort(key=len, reverse=True)
    return conglomerates


def calculate_conglomerate_indicators(conglomerate, votes_dict, total_votes_dict,
                                      total_political_votes, total_place_votes):
    """RUESP, RUESP_CAN e RCAN_UESP de um conglomerado."""
    cong_votes = sum(votes_dict.get(n, 0) for n in conglomerate)
    cong_total = sum(total_votes_dict.get(n, 0) for n in conglomerate)
    ruesp_can = cong_votes / total_political_votes if total_political_votes > 0 else 0
    rcan_uesp = cong_votes / cong_total if cong_total > 0 else 0
    ruesp = cong_total / total_place_votes if total_place_votes > 0 else 0
    return {
        "neighborhoods": sorted(list(conglomerate)),
        "size": len(conglomerate),
        "total_votes": cong_votes,
        "ruesp": round(ruesp, 6),
        "ruesp_can": round(ruesp_can, 6),
        "rcan_uesp": round(rcan_uesp, 6),
    }


def classify_conglomerate_importance(ruesp, qe_normalized):
    return "G" if ruesp > qe_normalized else "P"


def interpret_concentration(value: float) -> str:
    faixas = [
        (0.125, "irrisoria"), (0.25, "muito_baixa"), (0.375, "baixa"),
        (0.5, "media_baixa"), (0.625, "media"), (0.75, "media_alta"),
        (0.875, "alta"), (1.0, "muito_alta"),
    ]
    for lim, nome in faixas:
        if value < lim:
            return nome
    return "altissima"


def summarize_lq_hc(lq_hc: Dict[str, Dict[str, float]], display: Dict[str, str]):
    if not lq_hc:
        return {}
    lq_max_key = max(lq_hc, key=lambda k: lq_hc[k]["lq"])
    hc_pos = sum(v["hc"] for v in lq_hc.values() if v["hc"] > 0)
    ci_max_key = max(lq_hc, key=lambda k: lq_hc[k]["ci"])
    return {
        "lq_max": lq_hc[lq_max_key]["lq"],
        "bairro_lq_max": display.get(lq_max_key, lq_max_key),
        "hc_total_positivo": round(hc_pos, 2),
        "bairros_lq_acima_1": sum(1 for v in lq_hc.values() if v["lq"] > 1),
        "ci_max": lq_hc[ci_max_key]["ci"],
        "bairro_ci_max": display.get(ci_max_key, ci_max_key),
    }


# ----------------------------------------------------------------------------
# Carregamento dos dados (CSV, sem banco)
# ----------------------------------------------------------------------------
def load_section_to_neighborhood() -> Tuple[Dict[Tuple[str, str], str], Dict[str, str], int]:
    """(zona,secao) -> bairro_norm ; bairro_norm -> display ; nº bairros do município."""
    df = pd.read_csv(RIOINT_CSV, usecols=["municipio_id", "NR_ZONA", "NR_SECAO", "name_neighborhood"],
                     dtype=str)
    df = df[df["municipio_id"].astype(str).str.strip() == MUNICIPIO_ID]
    sec_map: Dict[Tuple[str, str], str] = {}
    display: Dict[str, str] = {}
    bairros: Set[str] = set()
    for zona, secao, bairro in zip(df["NR_ZONA"], df["NR_SECAO"], df["name_neighborhood"]):
        if pd.isna(bairro) or str(bairro).strip() == "":
            continue
        nb = norm(bairro)
        if nb == "":
            continue
        sec_map[(str(zona).strip(), str(secao).strip())] = nb
        display.setdefault(nb, str(bairro).strip())
        bairros.add(nb)
    return sec_map, display, len(bairros)


def load_neighbors_graph(display: Dict[str, str]) -> Dict[str, List[str]]:
    """Grafo de vizinhança em espaço normalizado; enriquece display map."""
    data = json.load(open(NEIGHBORS_JSON, encoding="utf-8")).get("neighbors", {})
    graph: Dict[str, List[str]] = {}
    for k, vs in data.items():
        kn = norm(k)
        display.setdefault(kn, str(k).strip())
        graph.setdefault(kn, [])
        for v in vs:
            vn = norm(v)
            display.setdefault(vn, str(v).strip())
            graph[kn].append(vn)
    return graph


def aggregate_votes(sec_map: Dict[Tuple[str, str], str]):
    """Uma passada (chunked) no arquivo grande, filtrando Rio + Vereador.

    Retorna:
      votes_by_cand: {nr: {bairro_norm: votos}}
      total_by_neigh: {bairro_norm: votos (todos os candidatos)}
      total_by_cand:  {nr: votos totais}
      name_by_cand:   {nr: NM_VOTAVEL}
    """
    votes_by_cand: Dict[str, Dict[str, int]] = {}
    total_by_neigh: Dict[str, int] = {}
    total_by_cand: Dict[str, int] = {}
    name_by_cand: Dict[str, str] = {}

    usecols = ["CD_MUNICIPIO", "CD_CARGO", "NR_ZONA", "NR_SECAO",
               "NR_VOTAVEL", "NM_VOTAVEL", "QT_VOTOS"]
    reader = pd.read_csv(VOTES_CSV, sep=";", usecols=usecols, dtype=str,
                         chunksize=CHUNK, encoding="utf-8")
    rows_seen = 0
    for chunk in reader:
        rows_seen += len(chunk)
        m = (chunk["CD_MUNICIPIO"].str.strip() == MUNICIPIO_ID) & \
            (chunk["CD_CARGO"].str.strip() == CD_CARGO)
        sub = chunk[m]
        if sub.empty:
            continue
        for zona, secao, nr, nm, qt in zip(sub["NR_ZONA"], sub["NR_SECAO"],
                                           sub["NR_VOTAVEL"], sub["NM_VOTAVEL"],
                                           sub["QT_VOTOS"]):
            nr = str(nr).strip()
            # Somente candidatos nominais (5 dígitos); exclui branco(95)/nulo(96)/legenda(2 díg.)
            if len(nr) != 5:
                continue
            bairro = sec_map.get((str(zona).strip(), str(secao).strip()))
            if bairro is None:
                continue
            try:
                q = int(qt)
            except (ValueError, TypeError):
                continue
            votes_by_cand.setdefault(nr, {})
            votes_by_cand[nr][bairro] = votes_by_cand[nr].get(bairro, 0) + q
            total_by_neigh[bairro] = total_by_neigh.get(bairro, 0) + q
            total_by_cand[nr] = total_by_cand.get(nr, 0) + q
            if nr not in name_by_cand:
                name_by_cand[nr] = str(nm).strip()
        print(f"  ... {rows_seen:,} linhas lidas", end="\r", flush=True)
    print()
    return votes_by_cand, total_by_neigh, total_by_cand, name_by_cand


def load_eleitos() -> List[Dict[str, str]]:
    """Vereadores eleitos em Rio de Janeiro 2024 (nr, urna, full, partido)."""
    df = pd.read_csv(ELEITOS_CSV, sep=";", encoding="latin-1", dtype=str)
    df = df[(df["sg_uf"] == UF) & (df["ds_cargo"] == "Vereador") &
            (df["ds_sit_totalizacao"] == "Eleito") & (df["nr_turno"] == "1")]
    df = df[df["nm_municipio"].map(lambda x: slugify(x)) == slugify(MUNICIPIO_NOME)]
    out = []
    for _, r in df.iterrows():
        out.append({
            "nr": str(int(float(r["nr_candidato"]))),
            "urna": str(r["nm_urna_candidato"]).strip(),
            "full": str(r["nm_candidato"]).strip(),
            "partido": str(r["sg_partido"]).strip(),
        })
    return out


def load_qe() -> float:
    df = pd.read_csv(QE_CSV, sep=";", encoding="latin-1")
    col_m = [c for c in df.columns if "unic" in c.lower()][0]
    col_q = [c for c in df.columns if "quociente" in c.lower()][0]
    sub = df[df[col_m].astype(str).str.upper().str.contains("RIO DE JANEIRO", na=False)]
    val = str(sub[col_q].iloc[0]).replace(".", "").replace(",", ".")
    return float(val)


# ----------------------------------------------------------------------------
# Análise por candidato (idêntica a analyze_political_concentration)
# ----------------------------------------------------------------------------
def analyze_candidate(nr, votes_dict, total_by_neigh, total_political_votes,
                      total_place_votes, total_neighborhoods, qe, neighbors,
                      display, sf) -> Dict[str, Any]:
    lq_hc = calculate_lq_hc(votes_dict, total_by_neigh, total_political_votes, total_place_votes)
    filtered = filter_significant_votes(votes_dict, qe, total_neighborhoods, THRESHOLD_PERCENT)
    classification = classify_neighborhood_count(len(filtered), total_neighborhoods)
    conglomerates = find_filtered_conglomerates(set(filtered.keys()), neighbors)

    qe_norm = qe / total_place_votes if total_place_votes > 0 else 0
    cong_results, fuzzy_results = [], []
    for i, cong in enumerate(conglomerates, 1):
        ind = calculate_conglomerate_indicators(cong, filtered, total_by_neigh,
                                                total_political_votes, total_place_votes)
        ind["importance"] = classify_conglomerate_importance(ind["ruesp"], qe_norm)
        entradas = {
            "ruesp_can": ind["ruesp_can"] * 100,
            "tam_conglomerado": min(ind["size"], 10),
            "qtd_bairros": min(len(filtered), 100),
        }
        try:
            fz = sf.inferir(entradas)
        except Exception:
            fz = 0.0
        ind["fuzzy_concentration"] = round(fz, 4)
        ind["id"] = i
        ind["neighborhoods"] = [display.get(n, n) for n in ind["neighborhoods"]]
        fuzzy_results.append(fz)
        cong_results.append(ind)

    concentracao = sum(fuzzy_results) / len(fuzzy_results) if fuzzy_results else 0.0
    lq_hc_disp = {display.get(k, k): v for k, v in lq_hc.items()}
    return {
        "total_votes": total_political_votes,
        "neighborhoods_with_votes": len(votes_dict),
        "neighborhoods_after_filter": len(filtered),
        "classification": classification,
        "conglomerates": cong_results,
        "lq_hc": lq_hc_disp,
        "lq_hc_summary": summarize_lq_hc(lq_hc, display),
        "concentracao_final": round(concentracao, 4),
        "interpretation": interpret_concentration(concentracao),
        "total_conglomerates": len(conglomerates),
    }


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(JSON_DIR, exist_ok=True)

    print("1) Mapa seção->bairro (RIOINT2024, Rio)...")
    sec_map, display, total_neighborhoods = load_section_to_neighborhood()
    print(f"   seções mapeadas: {len(sec_map):,} | bairros no município: {total_neighborhoods}")

    print("2) Grafo de vizinhança (Rio)...")
    neighbors = load_neighbors_graph(display)
    print(f"   bairros no grafo: {len(neighbors)}")

    print("3) Agregando votos (Rio, Vereador) do arquivo grande em chunks...")
    votes_by_cand, total_by_neigh, total_by_cand, name_by_cand = aggregate_votes(sec_map)
    total_place_votes = sum(total_by_neigh.values())
    print(f"   candidatos com votos: {len(votes_by_cand)} | total de votos nominais: {total_place_votes:,}")

    print("4) Eleitos + QE...")
    eleitos = load_eleitos()
    qe = load_qe()
    print(f"   eleitos: {len(eleitos)} | QE: {qe}")

    sf = SistemaFuzzyMamdani(
        arq_variaveis=os.path.join(FUZZY_DIR, "variaveis-fuzzy.json"),
        arq_regras=os.path.join(FUZZY_DIR, "regras-fuzzy.json"),
        defuzz="centroide",
    )

    summary_rows: List[Dict[str, Any]] = []
    bairro_rows: List[Dict[str, Any]] = []
    missing: List[Dict[str, str]] = []

    print("5) Analisando cada eleito...")
    for e in eleitos:
        nr = e["nr"]
        votes_dict = votes_by_cand.get(nr)
        if not votes_dict:
            missing.append(e)
            continue
        tot = total_by_cand.get(nr, 0)
        res = analyze_candidate(nr, votes_dict, total_by_neigh, tot, total_place_votes,
                                total_neighborhoods, qe, neighbors, display, sf)

        # maior conglomerado (já ordenado por tamanho) para a coluna "nossos indicadores"
        top = res["conglomerates"][0] if res["conglomerates"] else {}
        lqs = res["lq_hc_summary"]
        summary_rows.append({
            "nr": nr,
            "candidato": e["urna"],
            "full_name": e["full"],
            "partido": e["partido"],
            "total_votes": tot,
            "bairros_com_voto": res["neighborhoods_with_votes"],
            "bairros_filtrados": res["neighborhoods_after_filter"],
            "classificacao": res["classification"],
            "n_conglomerados": res["total_conglomerates"],
            "concentracao_fuzzy": res["concentracao_final"],
            "interpretacao": res["interpretation"],
            "top_cong_tam": top.get("size", 0),
            "top_cong_RCAN_UESP": top.get("rcan_uesp", 0),
            "top_cong_RUESP_CAN": top.get("ruesp_can", 0),
            "top_cong_RUESP": top.get("ruesp", 0),
            "LQ_max": lqs.get("lq_max"),
            "bairro_LQ_max": lqs.get("bairro_lq_max"),
            "bairros_LQ_acima_1": lqs.get("bairros_lq_acima_1"),
            "HC_total_positivo": lqs.get("hc_total_positivo"),
            "CI_max": lqs.get("ci_max"),
        })

        # linhas por bairro (compatível com candidates_vote_generate_maps.py)
        for bnorm, v_im in votes_dict.items():
            v_m = total_by_neigh.get(bnorm, 0)
            lh = res["lq_hc"].get(display.get(bnorm, bnorm), {})
            bairro_rows.append({
                "nome_candidato": e["urna"],
                "numero_candidato": nr,
                "partido": e["partido"],
                "bairro": display.get(bnorm, bnorm),
                "municipio_id": MUNICIPIO_ID,
                "municipio": "Rio de Janeiro",
                "UF": UF,
                "votos_absolutos_bairro": v_im,
                "votos_totais_bairro": v_m,
                "votos_totais_candidato": tot,
                "TOTAL_VOTOS_MUNICIPIO": total_place_votes,
                "RUESP(%)": round(v_m * 100 / total_place_votes, 6) if total_place_votes else 0,
                "RCAN_UESP(%)": round(v_im * 100 / v_m, 6) if v_m else 0,
                "RUESP_CAN(%)": round(v_im * 100 / tot, 6) if tot else 0,
                "LQ": lh.get("lq"),
                "HC": lh.get("hc"),
                "CI": lh.get("ci"),
            })

        # JSON detalhado
        with open(os.path.join(JSON_DIR, f"{nr}_{slugify(e['urna'])}.json"), "w", encoding="utf-8") as f:
            json.dump({"candidato": e, "qe": qe, **res}, f, ensure_ascii=False, indent=2)

    # ordenar summary por concentração fuzzy desc
    summary_rows.sort(key=lambda r: r["concentracao_fuzzy"], reverse=True)

    summary_path = os.path.join(OUT_DIR, "rio_vereadores_2024_fuzzy_summary.csv")
    with open(summary_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        w.writeheader()
        w.writerows(summary_rows)

    bairro_path = os.path.join(OUT_DIR, "rio_vereadores_2024_bairros.csv")
    with open(bairro_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(bairro_rows[0].keys()))
        w.writeheader()
        w.writerows(bairro_rows)

    print(f"\nOK. Eleitos analisados: {len(summary_rows)} | sem match no votação: {len(missing)}")
    if missing:
        print("  Sem match:", [f"{m['urna']}({m['nr']})" for m in missing])
    print(f"Resumo:  {summary_path}")
    print(f"Bairros: {bairro_path}")
    print(f"JSONs:   {JSON_DIR}/")


if __name__ == "__main__":
    main()
