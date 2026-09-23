import csv
import datetime
import re
import shutil
import unicodedata
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, Iterable, List, Optional, Tuple


DATA_DIR = Path("data")
YEARS = [2016, 2018, 2020, 2022, 2024]
EMENDAS_FILE = DATA_DIR / "EmendasArquivoGeral_com_candidatos.csv"

MAP_COLUMNS = ["nome_bairro_mapa", "id_bairro_mapa", "nome_arquivo_mapa"]
EMENDA_COLUMN = "nome_bairro_emenda"


RioKey = Tuple[str, str, str, str, str, str]
EmendaKey = Tuple[str, str, str]


def detect_csv_dialect(file_path: Path) -> csv.Dialect:
    with file_path.open("r", encoding="utf-8", newline="") as fh:
        sample = fh.read(64 * 1024)
    try:
        return csv.Sniffer().sniff(sample, delimiters=";,")
    except csv.Error:
        return csv.excel


def normalize_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"[_\-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_number_like(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""

    normalized = raw.replace(",", ".")
    if re.fullmatch(r"-?\d+(?:\.0+)?", normalized):
        try:
            return str(int(float(normalized)))
        except ValueError:
            return raw
    return raw


def safe_get(row: Dict[str, str], key: str) -> str:
    value = row.get(key, "")
    return str(value).strip() if value is not None else ""


def build_rio_key_from_row(row: Dict[str, str]) -> RioKey:
    return (
        safe_get(row, "NM_MUNICIPIO"),
        normalize_number_like(safe_get(row, "municipio_id")),
        normalize_number_like(safe_get(row, "NR_SECAO")),
        normalize_number_like(safe_get(row, "NR_ZONA")),
        safe_get(row, "NM_LOCAL_VOTACAO"),
        safe_get(row, "DS_LOCAL_VOTACAO_ENDERECO"),
    )


def build_local_key_from_row(row: Dict[str, str]) -> RioKey:
    return (
        safe_get(row, "municipio"),
        normalize_number_like(safe_get(row, "municipio_id")),
        normalize_number_like(safe_get(row, "seção")),
        normalize_number_like(safe_get(row, "zona")),
        safe_get(row, "local_votacao"),
        safe_get(row, "address"),
    )


def build_emenda_key(municipio: str, uf: str, bairro: str) -> EmendaKey:
    return (normalize_text(municipio), normalize_text(uf), normalize_text(bairro))


def load_rio_index(year: int) -> Dict[RioKey, Tuple[str, str, str]]:
    rio_file = DATA_DIR / f"RIOINT{year}.csv"
    if not rio_file.exists():
        print(f"[WARN] Arquivo RIO ausente para {year}: {rio_file}")
        return {}

    dialect = detect_csv_dialect(rio_file)
    index: Dict[RioKey, Tuple[str, str, str]] = {}
    with rio_file.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, dialect=dialect)
        for row in reader:
            key = build_rio_key_from_row(row)
            if key not in index:
                index[key] = (
                    safe_get(row, "name_neighborhood"),
                    safe_get(row, "id_do_bairro"),
                    safe_get(row, "arquivo_mapa"),
                )
    return index


def load_emendas_index() -> Dict[EmendaKey, str]:
    if not EMENDAS_FILE.exists():
        print(f"[WARN] Arquivo de emendas nao encontrado: {EMENDAS_FILE}")
        return {}

    dialect = detect_csv_dialect(EMENDAS_FILE)
    index: Dict[EmendaKey, str] = {}
    with EMENDAS_FILE.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, dialect=dialect)
        for row in reader:
            municipio = safe_get(row, "MUNICIPIO")
            uf = safe_get(row, "UF")
            bairro = safe_get(row, "BAIRRO")
            if not municipio or not uf or not bairro:
                continue

            key = build_emenda_key(municipio=municipio, uf=uf, bairro=bairro)
            if key not in index:
                # Manter exatamente como escrito no arquivo de origem.
                index[key] = bairro
    return index


def ensure_columns(fieldnames: List[str]) -> List[str]:
    result = list(fieldnames)
    for column in MAP_COLUMNS + [EMENDA_COLUMN]:
        if column not in result:
            result.append(column)
    return result


def process_local_file(
    year: int,
    rio_index: Dict[RioKey, Tuple[str, str, str]],
    emendas_index: Dict[EmendaKey, str],
) -> Dict[str, int]:
    local_file = DATA_DIR / f"local_votacao_BRASIL_{year}.csv"
    stats = {
        "rows": 0,
        "map_match": 0,
        "emenda_match": 0,
        "missing_map": 0,
        "missing_emenda": 0,
    }

    if not local_file.exists():
        print(f"[WARN] Arquivo local_votacao ausente para {year}: {local_file}")
        return stats

    dialect = detect_csv_dialect(local_file)
    with local_file.open("r", encoding="utf-8", newline="") as infile:
        reader = csv.DictReader(infile, dialect=dialect)
        fieldnames = ensure_columns(list(reader.fieldnames or []))

        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            delete=False,
            dir=str(local_file.parent),
        ) as tmp:
            writer = csv.DictWriter(
                tmp,
                fieldnames=fieldnames,
                delimiter=dialect.delimiter,
                quotechar=dialect.quotechar,
                quoting=dialect.quoting,
                lineterminator="\n",
            )
            writer.writeheader()

            for row in reader:
                stats["rows"] += 1

                rio_key = build_local_key_from_row(row)
                rio_values = rio_index.get(rio_key)
                if rio_values is not None:
                    row["nome_bairro_mapa"], row["id_bairro_mapa"], row["nome_arquivo_mapa"] = rio_values
                    stats["map_match"] += 1
                else:
                    row["nome_bairro_mapa"] = ""
                    row["id_bairro_mapa"] = ""
                    row["nome_arquivo_mapa"] = ""
                    stats["missing_map"] += 1

                emenda_key = build_emenda_key(
                    municipio=safe_get(row, "municipio"),
                    uf=safe_get(row, "UF"),
                    bairro=safe_get(row, "bairro"),
                )
                emenda_bairro = emendas_index.get(emenda_key, "")
                row[EMENDA_COLUMN] = emenda_bairro
                if emenda_bairro:
                    stats["emenda_match"] += 1
                else:
                    stats["missing_emenda"] += 1

                writer.writerow(row)

    shutil.move(tmp.name, local_file)
    return stats


def print_stats(year: int, stats: Dict[str, int]) -> None:
    print(
        f"{year}: linhas={stats['rows']}, "
        f"map_match={stats['map_match']}, emenda_match={stats['emenda_match']}, "
        f"sem_map={stats['missing_map']}, sem_emenda={stats['missing_emenda']}"
    )


def aggregate_stats(stats_list: Iterable[Dict[str, int]]) -> Dict[str, int]:
    total = {"rows": 0, "map_match": 0, "emenda_match": 0, "missing_map": 0, "missing_emenda": 0}
    for stats in stats_list:
        for key in total:
            total[key] += stats[key]
    return total


def main() -> None:
    start = datetime.datetime.now()
    print(f"\nStarted script running at {start}\n")

    emendas_index = load_emendas_index()
    print(f"Indice de emendas carregado: {len(emendas_index)} chaves")

    rio_index_by_year: Dict[int, Dict[RioKey, Tuple[str, str, str]]] = {}
    for year in YEARS:
        rio_index_by_year[year] = load_rio_index(year)
        print(f"Indice RIO {year}: {len(rio_index_by_year[year])} chaves")

    all_stats: List[Dict[str, int]] = []
    for year in YEARS:
        year_stats = process_local_file(
            year=year,
            rio_index=rio_index_by_year.get(year, {}),
            emendas_index=emendas_index,
        )
        all_stats.append(year_stats)
        print_stats(year, year_stats)

    total = aggregate_stats(all_stats)
    print(
        "\nResumo final: "
        f"linhas_total={total['rows']}, "
        f"map_match_total={total['map_match']}, "
        f"emenda_match_total={total['emenda_match']}, "
        f"sem_map_total={total['missing_map']}, "
        f"sem_emenda_total={total['missing_emenda']}"
    )
    print(f"Finished script running in {datetime.datetime.now() - start}\n")


if __name__ == "__main__":
    main()
