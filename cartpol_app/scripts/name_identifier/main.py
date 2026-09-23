import csv
import json
import os
import time
from pathlib import Path

import openai
import requests
from rapidfuzz import fuzz, process

SCRIPT_DIR = Path(__file__).parent
NAME_LIST = SCRIPT_DIR / "name_list.txt"
CSV_2010 = SCRIPT_DIR / "nomes_2010.csv"
CSV_2014 = SCRIPT_DIR / "nomes_2014.csv"
OUTPUT = SCRIPT_DIR / "output.csv"

COMMITTEE_PREFIXES = ("COM,", "COMISSAO", "COM ")

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; research-bot/1.0)"}


def load_csv(path: Path, year: int) -> list[dict]:
    rows = []
    with open(path, encoding="latin-1") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            row["ANO"] = year
            rows.append(row)
    return rows


def is_committee(name: str) -> bool:
    upper = name.strip().upper()
    return any(upper.startswith(p) for p in COMMITTEE_PREFIXES)


def search_camara(name: str) -> str:
    url = f"https://www.camara.leg.br/busca-geral?termo={requests.utils.quote(name)}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        # Return first 3000 chars of text (HTML) as context for the model
        return r.text[:5000]
    except Exception as e:
        return f"Error: {e}"


def search_senado(name: str) -> str:
    url = f"https://www6g.senado.leg.br/busca/?portal=Senadores&q={requests.utils.quote(name)}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        return r.text[:5000]
    except Exception as e:
        return f"Error: {e}"


def lookup_csv(name: str, year: int, all_candidates: list[dict]) -> list[dict]:
    year_candidates = [c for c in all_candidates if c["ANO"] == year]
    query = name.upper()

    scored = []
    for candidate in year_candidates:
        score_nm = fuzz.token_set_ratio(query, candidate["NM_CANDIDATO"])
        score_urna = fuzz.token_set_ratio(query, candidate.get("NM_URNA_CANDIDATO", ""))
        best_score = max(score_nm, score_urna)
        if best_score >= 70:
            scored.append({**candidate, "SCORE": best_score})

    scored.sort(key=lambda x: x["SCORE"], reverse=True)
    return scored[:5]


def process_tool_call(tool_name: str, tool_input: dict, all_candidates: list[dict]) -> str:
    if tool_name == "search_camara":
        time.sleep(1)
        return search_camara(tool_input["name"])
    elif tool_name == "search_senado":
        time.sleep(1)
        return search_senado(tool_input["name"])
    elif tool_name == "lookup_csv":
        results = lookup_csv(tool_input["name"], tool_input["year"], all_candidates)
        return json.dumps(results, ensure_ascii=False)
    return "Unknown tool"


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_camara",
            "description": (
                "Search the Brazilian Chamber of Deputies website for a candidate by name. "
                "Returns HTML content with search results. Use to determine if a person is a federal deputy."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "The candidate name to search for"}
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_senado",
            "description": (
                "Search the Brazilian Senate website for a senator by name. "
                "Returns HTML content with search results. Use to determine if a person is a senator."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "The senator name to search for"}
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_csv",
            "description": (
                "Look up a candidate in the local election CSV data for a given year. "
                "Searches both NM_CANDIDATO (full name) and NM_URNA_CANDIDATO (ballot name). "
                "Returns fuzzy-matched candidates with fields: NM_CANDIDATO, NM_URNA_CANDIDATO, NR_CANDIDATO, SG_PARTIDO, DS_CARGO, SG_UF, ANO."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "The candidate name to search for"},
                    "year": {
                        "type": "integer",
                        "description": "Election year: 2010 or 2014",
                        "enum": [2010, 2014],
                    },
                },
                "required": ["name", "year"],
            },
        },
    },
]

SYSTEM_PROMPT = """You are a Brazilian political data assistant. Your task is to identify candidates for federal deputy (Deputado Federal) or senator (Senador) from a given name, and find their official data in election CSV files.

For each name provided:
1. First check if the name looks like a committee (starts with "COM," or "COMISSAO") — if so, respond immediately with: {"status": "committee"}
2. Otherwise, search the Camara and Senado websites to determine if the person is a deputy or senator, and in which election year (2010 or 2014).
3. Then use lookup_csv to find their official record. Try the most likely year first (most recent if unsure). If not found, try the other year.
4. Return a JSON object with: {"status": "found", "NM_CANDIDATO": "...", "NM_URNA_CANDIDATO": "...", "NR_CANDIDATO": "...", "SG_PARTIDO": "...", "DS_CARGO": "...", "SG_UF": "...", "ANO": YYYY}
5. If you cannot find the candidate after searching both years, return: {"status": "not_found"}

Always respond with ONLY the final JSON object as your last message (no extra text). The CSV data covers elections for 2010 and 2014 only."""


def run_agent(client: openai.OpenAI, name: str, all_candidates: list[dict]) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Find the official election data for: {name}"},
    ]

    for _ in range(10):  # max iterations
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )

        msg = response.choices[0].message
        # Convert to dict so the list stays homogeneous for the next API call
        assistant_msg: dict = {"role": "assistant", "content": msg.content}
        if msg.tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in msg.tool_calls
            ]
        messages.append(assistant_msg)

        if response.choices[0].finish_reason == "stop":
            text = (msg.content or "").strip()
            try:
                start = text.find("{")
                end = text.rfind("}") + 1
                if start >= 0 and end > start:
                    return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
            return {"status": "not_found"}

        if response.choices[0].finish_reason == "tool_calls":
            for tool_call in (msg.tool_calls or []):
                tool_input = json.loads(tool_call.function.arguments)
                result = process_tool_call(tool_call.function.name, tool_input, all_candidates)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

    return {"status": "not_found"}


def main():
    print("Loading CSVs...")
    candidates_2010 = load_csv(CSV_2010, 2010)
    candidates_2014 = load_csv(CSV_2014, 2014)
    all_candidates = candidates_2010 + candidates_2014
    print(f"Loaded {len(candidates_2010)} candidates from 2010, {len(candidates_2014)} from 2014")

    names = [line.strip() for line in NAME_LIST.read_text().splitlines() if line.strip()]
    print(f"Processing {len(names)} names...")

    client = openai.OpenAI()

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["NOME_LISTA", "NM_CANDIDATO", "NM_URNA_CANDIDATO", "NR_CANDIDATO", "SG_PARTIDO", "DS_CARGO", "SG_UF", "ANO", "STATUS"],
        )
        writer.writeheader()

        for i, name in enumerate(names, 1):
            print(f"[{i}/{len(names)}] {name}")

            if is_committee(name):
                writer.writerow({
                    "NOME_LISTA": name,
                    "NM_CANDIDATO": "",
                    "NM_URNA_CANDIDATO": "",
                    "NR_CANDIDATO": "",
                    "SG_PARTIDO": "",
                    "DS_CARGO": "",
                    "SG_UF": "",
                    "ANO": "",
                    "STATUS": "committee",
                })
                print("  -> committee (skipped)")
                continue

            try:
                result = run_agent(client, name, all_candidates)
                status = result.get("status", "not_found")
                writer.writerow({
                    "NOME_LISTA": name,
                    "NM_CANDIDATO": result.get("NM_CANDIDATO", ""),
                    "NM_URNA_CANDIDATO": result.get("NM_URNA_CANDIDATO", ""),
                    "NR_CANDIDATO": result.get("NR_CANDIDATO", ""),
                    "SG_PARTIDO": result.get("SG_PARTIDO", ""),
                    "DS_CARGO": result.get("DS_CARGO", ""),
                    "SG_UF": result.get("SG_UF", ""),
                    "ANO": result.get("ANO", ""),
                    "STATUS": status,
                })
                print(f"  -> {status}: {result.get('NM_CANDIDATO', '')} ({result.get('DS_CARGO', '')})")
            except Exception as e:
                print(f"  -> ERROR: {e}")
                writer.writerow({
                    "NOME_LISTA": name,
                    "NM_CANDIDATO": "",
                    "NM_URNA_CANDIDATO": "",
                    "NR_CANDIDATO": "",
                    "SG_PARTIDO": "",
                    "DS_CARGO": "",
                    "SG_UF": "",
                    "ANO": "",
                    "STATUS": f"error: {e}",
                })

            f.flush()

    print(f"\nDone! Results saved to {OUTPUT}")


if __name__ == "__main__":
    main()
