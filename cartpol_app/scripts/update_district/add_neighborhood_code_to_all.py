import csv
import datetime
import re
import shutil
import unicodedata
import zipfile
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, List, Optional, Tuple


DATA_DIR = Path("data")
MAPS_COUNTY_DIR = Path("/home/iuri/TCC/cartpol-pwa/src/assets/maps/county")
MAPS_INDEX_JS = Path("/home/iuri/TCC/cartpol-pwa/src/assets/maps/index.js")
TARGET_GLOB = "RIO*.csv"

ID_CANDIDATES = ("CD_BAIRRO", "code_neigh")
NAME_CANDIDATES = ("NM_BAIRRO", "name_neigh", "NM_SUBDIST", "name_subdi")


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


def parse_dbf_records_from_bytes(data: bytes) -> Tuple[List[str], List[Dict[str, str]]]:
    if len(data) < 32:
        return [], []

    header_len = int.from_bytes(data[8:10], "little")
    record_len = int.from_bytes(data[10:12], "little")
    if header_len <= 32 or record_len <= 1:
        return [], []

    fields: List[Tuple[str, int]] = []
    cursor = 32
    while cursor + 32 <= len(data):
        if data[cursor] == 0x0D:
            break
        raw_name = data[cursor:cursor + 11]
        field_name = raw_name.split(b"\x00", 1)[0].decode("latin-1", errors="ignore").strip()
        field_length = data[cursor + 16]
        if field_name:
            fields.append((field_name, field_length))
        cursor += 32

    field_names = [name for name, _ in fields]
    records: List[Dict[str, str]] = []
    offset = header_len
    encodings = ("utf-8", "cp1252", "latin-1")

    while offset + record_len <= len(data):
        row_bytes = data[offset:offset + record_len]
        offset += record_len
        if not row_bytes or row_bytes[0:1] == b"*":
            continue

        row: Dict[str, str] = {}
        value_cursor = 1
        for field_name, field_length in fields:
            raw_value = row_bytes[value_cursor:value_cursor + field_length]
            value_cursor += field_length

            value_text = ""
            for encoding in encodings:
                try:
                    value_text = raw_value.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            value_text = value_text.strip().strip("\x00")
            row[field_name] = value_text

        records.append(row)

    return field_names, records


def detect_field(field_names: List[str], candidates: Tuple[str, ...]) -> Optional[str]:
    for candidate in candidates:
        if candidate in field_names:
            return candidate
    lowered = {name.lower(): name for name in field_names}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    return None


def load_map_neighborhood_index(zip_path: Path) -> Tuple[Dict[str, str], Optional[str], Optional[str]]:
    with zipfile.ZipFile(zip_path, "r") as zf:
        dbf_files = [name for name in zf.namelist() if name.lower().endswith(".dbf")]
        if not dbf_files:
            return {}, None, None
        dbf_data = zf.read(dbf_files[0])

    field_names, records = parse_dbf_records_from_bytes(dbf_data)
    id_field = detect_field(field_names, ID_CANDIDATES)
    name_field = detect_field(field_names, NAME_CANDIDATES)
    if not id_field or not name_field:
        return {}, id_field, name_field

    neighborhood_to_id: Dict[str, str] = {}
    for record in records:
        raw_name = record.get(name_field, "")
        raw_id = record.get(id_field, "")
        normalized_name = normalize_text(raw_name)
        if not normalized_name or raw_id in ("", None):
            continue
        if normalized_name not in neighborhood_to_id:
            neighborhood_to_id[normalized_name] = str(raw_id).strip()

    return neighborhood_to_id, id_field, name_field


def build_maps_index_from_js() -> Tuple[Dict[str, str], Dict[str, str]]:
    if not MAPS_INDEX_JS.exists():
        return {}, {}

    content = MAPS_INDEX_JS.read_text(encoding="utf-8", errors="ignore")

    import_pattern = re.compile(
        r'import\s+(zip[\w]+)\s+from\s+"\.\/county\/([^"]+\.zip)";'
    )
    key_pattern = re.compile(r"(\d+)\s*:\s*(zip[\w]+)")

    var_to_filename: Dict[str, str] = {}
    for var_name, filename in import_pattern.findall(content):
        var_to_filename[var_name] = filename

    id_to_filename: Dict[str, str] = {}
    for county_id, var_name in key_pattern.findall(content):
        filename = var_to_filename.get(var_name)
        if filename and (MAPS_COUNTY_DIR / filename).exists():
            id_to_filename[county_id] = filename

    return id_to_filename, var_to_filename


def build_maps_name_index() -> Dict[str, str]:
    name_to_file: Dict[str, str] = {}
    for zip_path in MAPS_COUNTY_DIR.glob("*.zip"):
        normalized = normalize_text(zip_path.stem)
        if normalized and normalized not in name_to_file:
            name_to_file[normalized] = zip_path.name
    return name_to_file


def resolve_map_filename(
    municipio: str,
    municipio_id: str,
    id_to_filename: Dict[str, str],
    name_to_filename: Dict[str, str],
) -> str:
    clean_id = str(municipio_id).strip()
    if clean_id in id_to_filename:
        return id_to_filename[clean_id]
    return name_to_filename.get(normalize_text(municipio), "")


def detect_csv_dialect(file_path: Path) -> csv.Dialect:
    with file_path.open("r", encoding="utf-8", newline="") as fh:
        sample = fh.read(64 * 1024)
    try:
        return csv.Sniffer().sniff(sample, delimiters=";,")
    except csv.Error:
        return csv.excel


def process_csv_file(
    csv_path: Path,
    id_to_filename: Dict[str, str],
    name_to_filename: Dict[str, str],
    cache_map_index: Dict[str, Dict[str, str]],
) -> Dict[str, int]:
    dialect = detect_csv_dialect(csv_path)
    stats = {
        "rows": 0,
        "map_found": 0,
        "neighborhood_id_found": 0,
        "missing_map": 0,
        "missing_neighborhood_id": 0,
    }

    with csv_path.open("r", encoding="utf-8", newline="") as infile:
        reader = csv.DictReader(infile, dialect=dialect)
        fieldnames = list(reader.fieldnames or [])

        if "id_do_bairro" not in fieldnames:
            fieldnames.append("id_do_bairro")
        if "arquivo_mapa" not in fieldnames:
            fieldnames.append("arquivo_mapa")

        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            delete=False,
            dir=str(csv_path.parent),
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
                municipio = row.get("NM_MUNICIPIO", "")
                municipio_id = row.get("municipio_id", "")
                neighborhood_name = row.get("name_neighborhood", "")

                map_filename = resolve_map_filename(
                    municipio=municipio,
                    municipio_id=municipio_id,
                    id_to_filename=id_to_filename,
                    name_to_filename=name_to_filename,
                )
                row["arquivo_mapa"] = map_filename

                neighborhood_id = ""
                if map_filename:
                    stats["map_found"] += 1
                    if map_filename not in cache_map_index:
                        zip_file_path = MAPS_COUNTY_DIR / map_filename
                        neighborhood_index, id_field, name_field = load_map_neighborhood_index(
                            zip_file_path
                        )
                        cache_map_index[map_filename] = neighborhood_index
                        if not id_field or not name_field:
                            print(
                                f"[WARN] Campos ausentes em {map_filename}: "
                                f"id_field={id_field}, name_field={name_field}"
                            )

                    neighborhood_id = cache_map_index[map_filename].get(
                        normalize_text(neighborhood_name), ""
                    )
                else:
                    stats["missing_map"] += 1

                if neighborhood_id:
                    stats["neighborhood_id_found"] += 1
                else:
                    stats["missing_neighborhood_id"] += 1
                row["id_do_bairro"] = neighborhood_id
                writer.writerow(row)

    shutil.move(tmp.name, csv_path)
    return stats


def main() -> None:
    start_time = datetime.datetime.now()
    print(f"\nStarted script running at {start_time}\n")

    if not MAPS_COUNTY_DIR.exists():
        raise FileNotFoundError(f"Diretorio de mapas nao encontrado: {MAPS_COUNTY_DIR}")

    id_to_filename, _ = build_maps_index_from_js()
    name_to_filename = build_maps_name_index()

    csv_files = sorted(DATA_DIR.glob(TARGET_GLOB))
    if not csv_files:
        print(f"Nenhum arquivo encontrado para padrao {TARGET_GLOB} em {DATA_DIR}")
        return

    map_cache: Dict[str, Dict[str, str]] = {}
    total = {
        "rows": 0,
        "map_found": 0,
        "neighborhood_id_found": 0,
        "missing_map": 0,
        "missing_neighborhood_id": 0,
    }

    for csv_file in csv_files:
        print(f"Processando {csv_file}...")
        file_stats = process_csv_file(
            csv_path=csv_file,
            id_to_filename=id_to_filename,
            name_to_filename=name_to_filename,
            cache_map_index=map_cache,
        )
        print(
            f"  linhas={file_stats['rows']}, mapas={file_stats['map_found']}, "
            f"ids={file_stats['neighborhood_id_found']}, "
            f"sem_mapa={file_stats['missing_map']}, "
            f"sem_id_bairro={file_stats['missing_neighborhood_id']}"
        )
        for key in total:
            total[key] += file_stats[key]

    print("\nResumo final:")
    print(f"  linhas_total={total['rows']}")
    print(f"  mapas_encontrados={total['map_found']}")
    print(f"  ids_bairro_encontrados={total['neighborhood_id_found']}")
    print(f"  linhas_sem_mapa={total['missing_map']}")
    print(f"  linhas_sem_id_bairro={total['missing_neighborhood_id']}")

    elapsed = datetime.datetime.now() - start_time
    print(f"\nFinished script running\nTotal time: {elapsed}\n")


if __name__ == "__main__":
    main()
