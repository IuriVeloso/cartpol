"""
Script para enriquecer o output.csv com NM_URNA_CANDIDATO.

Lê o arquivo output.csv, verifica o ANO de cada candidato (entre 2010 e 2014)
e busca o NM_URNA_CANDIDATO nos CSVs correspondentes (nomes_2010.csv, nomes_2014.csv).
Atualiza as linhas que estiverem sem NM_URNA_CANDIDATO.
"""

import csv
from pathlib import Path

from rapidfuzz import fuzz

SCRIPT_DIR = Path(__file__).parent
OUTPUT = SCRIPT_DIR / "output.csv"
CSV_2010 = SCRIPT_DIR / "nomes_2010.csv"
CSV_2014 = SCRIPT_DIR / "nomes_2014.csv"

# Ano 2011, 2012 usam dados de 2010; 2013 usa dados de 2014
YEAR_TO_CSV = {2010: CSV_2010, 2011: CSV_2010, 2012: CSV_2010, 2013: CSV_2014, 2014: CSV_2014}


def load_csv(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="latin-1") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            rows.append(row)
    return rows


def lookup_candidate(name: str, candidates: list[dict], min_score: int = 70) -> dict | None:
    """Busca candidato por nome (NM_CANDIDATO ou NM_URNA_CANDIDATO) com fuzzy matching."""
    if not name or not name.strip():
        return None
    query = name.upper()
    best_match = None
    best_score = 0

    for c in candidates:
        score_nm = fuzz.token_set_ratio(query, c.get("NM_CANDIDATO", ""))
        score_urna = fuzz.token_set_ratio(query, c.get("NM_URNA_CANDIDATO", ""))
        score = max(score_nm, score_urna)
        if score >= min_score and score > best_score:
            best_score = score
            best_match = c

    return best_match


def main():
    # Carrega CSVs únicos (2010 e 2014)
    candidates_by_year: dict[int, list[dict]] = {}
    for year in (2010, 2014):
        path = YEAR_TO_CSV[year]
        if path.exists():
            data = load_csv(path)
            for y, p in YEAR_TO_CSV.items():
                if p == path:
                    candidates_by_year[y] = data

    # Lê o output
    rows = []
    fieldnames = []
    with open(OUTPUT, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    # Garante que NM_URNA_CANDIDATO existe nas colunas
    if "NM_URNA_CANDIDATO" not in fieldnames:
        # Insere após NM_CANDIDATO
        idx = fieldnames.index("NM_CANDIDATO") + 1 if "NM_CANDIDATO" in fieldnames else 1
        fieldnames.insert(idx, "NM_URNA_CANDIDATO")

    updated = 0
    for row in rows:
        row.setdefault("NM_URNA_CANDIDATO", "")
        nm_urna = str(row.get("NM_URNA_CANDIDATO", "") or "").strip()
        ano_str = row.get("ANO", "").strip()

        # Se já tem NM_URNA_CANDIDATO, pula
        if nm_urna:
            continue

        # Extrai ano
        try:
            ano = int(ano_str)
        except (ValueError, TypeError):
            continue

        if ano not in YEAR_TO_CSV or ano not in candidates_by_year:
            continue

        # Busca por NOME_LISTA ou NM_CANDIDATO
        search_name = row.get("NOME_LISTA", "") or row.get("NM_CANDIDATO", "")
        if not search_name.strip():
            continue

        match = lookup_candidate(search_name, candidates_by_year[ano])
        if match and match.get("NM_URNA_CANDIDATO"):
            row["NM_URNA_CANDIDATO"] = match["NM_URNA_CANDIDATO"]
            updated += 1
            print(f"  Encontrado: {search_name} -> {match['NM_URNA_CANDIDATO']}")

    # Escreve o output atualizado
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"\nAtualizados {updated} registros com NM_URNA_CANDIDATO. Salvo em {OUTPUT}")


if __name__ == "__main__":
    main()
