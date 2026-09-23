"""
Roda o fuzzy municipal (por bairros) para vereadores eleitos em 2020
apenas para 1 município do RJ (default: Niterói), restrito aos municípios com mapa.

Entradas:
- Eleitos: votacao_candidato-municipio_prefeito_2020_rj.csv
- QE: quociente_eleitoral-uf_vereador_2020_rj.csv
- Vizinhança por bairros: neighborhoods/rj/neighbors_<municipio>_bairros.json

Saídas:
- results/test_<municipio>_vereadores_eleitos_2020.csv
- results/test_<municipio>_unmatched_2020.json
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import unicodedata
from typing import Any, Dict, List, Optional

import pandas as pd

# Garantir imports do projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cartpol.settings")

import django

django.setup()

from cartpol_app.models import County, Political
from cartpol_app.scripts.conglomerates.politics_analysis import analyze_political_concentration


QE_CSV = os.path.join(
    BASE_DIR,
    "cartpol_app",
    "scripts",
    "conglomerates",
    "quociente_eleitoral-uf_vereador_2020_rj.csv",
)
ELEITOS_CSV = os.path.join(
    BASE_DIR,
    "cartpol_app",
    "scripts",
    "conglomerates",
    "votacao_candidato-municipio_prefeito_2020_rj.csv",
)
MAP_INDEX = os.path.join(
    BASE_DIR,
    "cartpol_app",
    "scripts",
    "conglomerates",
    "neighborhoods",
    "rj",
    "index.json",
)


_TITULOS = {
    "DR", "DRA", "DRA.", "DOUTOR", "DOUTORA",
    "PROFESSOR", "PROFESSORA", "PROF",
    "PASTOR", "PASTORA",
    "CABO", "SARGENTO", "SOLDADO", "DELEGADO", "VEREADOR",
    "ENFERMEIRO", "ENFERMEIRA", "MÉDICO", "MEDICO",
    "SUB", "DJ", "GU",
}

# Correções manuais por nome de urna exato (upper), para casos que a heurística não resolve
_GENERO_MANUAL: Dict[str, str] = {
    "SARGENTO THIMOTEO": "masculino",
    "PASTOR VALTER DA RADIO": "masculino",
    "TEIXEIRA DO CARVÃO": "masculino",
    "RODRIGO COM A FORÇA DO POVO": "masculino",
    "RODRIGO GOMES": "masculino",
    "CABO ALONSIMAR": "masculino",
    "DR ABDU NEME": "masculino",
    "PROFESSOR WAINER": "masculino",
    "PASTOR MARCOS ELIAS": "masculino",
    "MICHELE TAVARES": "feminino",
    "DR MAURÍCIO": "masculino",
    "MARCOS ARAUJO": "masculino",
    "DR MARLON": "masculino",
    "DRA. MAYARA REZENDE": "feminino",
    "DRA MAYARA REZENDE": "feminino",
    "DRA, MAYARA REZENDE": "feminino",
    "FABIANO GONÇALVES": "masculino",
    "SYLVIO": "masculino",
    "ALLAN LYRA": "masculino",
    "RODRIGO FARAH": "masculino",
    "DOUGLAS GOMES": "masculino",
    "PROFESSOR TULIO": "masculino",
    "MANINHO DE CABUÇU": "masculino",
    "DR MANOEL BARRETO(MANOELZINHO)": "masculino",
    "DR ROBERTINHO": "masculino",
    "DOUGLAS NADAES": "masculino",
    "DJ DENILSO": "masculino",
    "PROFESSOR WILSON": "masculino",
    "GU SALIM": "masculino",
    "PITIQUINHO": "masculino",
    "DRA RENATA": "feminino",
    "RODRIGO PIT": "masculino",
    "PROFESSOR JEAN PIERRE": "masculino",
    "DR AMORIM": "masculino",
    "PROFESSORA AMANDA": "feminino",
    # 2020 — femininos evidentes
    "LUCIANA VALVERDE": "feminino",
    "KÁTIA MIKI": "feminino",
    "ROSELI ENFERMEIRA": "feminino",
    "LUCIANA ALVES": "feminino",
    "PAOLA DA PIZZARIA": "feminino",
    "NELCI PRAÇA": "feminino",
    "CRISTIANE DO SOBREIRA": "feminino",
    "LUCIARA AMIL": "feminino",
    "DEISI DO SEU DINO": "feminino",
    "LEIDE": "feminino",
    "MARCILEY LESSA": "feminino",
    "IZA VICENTE": "feminino",
    "VERONICA LIMA": "feminino",
    "MARIA ROSA": "feminino",
    "DRA RAQUEL": "feminino",
    "CICI MALDONADO": "feminino",
    "PRISCILLA CANEDO": "feminino",
    "MARIOLA": "feminino",
    "DRA LETICIA COSTA": "feminino",
    "MICA": "feminino",
    # 2020 — masculinos evidentes
    "RUBINHO METALURGICO": "masculino",
    "JORGE EDUARDO MASCOTE": "masculino",
    "BRANCO": "masculino",
    "TOSTÃO": "masculino",
    "FURLANI": "masculino",
    "CLEBINHO REIS": "masculino",
    "FABIO RIBEIRO": "masculino",
    "ALVARO CESAR": "masculino",
    "TONY SIQUEIRA": "masculino",
    "DANILO DO MERCADO": "masculino",
    "ARTHUR MONTEIRO": "masculino",
    "CELSO DO ALBA": "masculino",
    "ELBER CORREA": "masculino",
    "RAMON VIEIRA": "masculino",
    "MARCÃO DA SAÚDE": "masculino",
    "NINO DA AUTO ESCOLA": "masculino",
    "THALES COUTINHO": "masculino",
    "GEORGE JARDIM": "masculino",
    "RUSSÃO GOMES": "masculino",
    "FARRUSQUINHA": "masculino",
    "ALVINHO": "masculino",
    "BOECHAT": "masculino",
    "FELIPINHO RAVIS": "masculino",
    "WILLIAN CARVALHO": "masculino",
    "RENAN SCHIAVO": "masculino",
    "RENAN MARASSI": "masculino",
    "HICK SENE": "masculino",
    "IVAN MELO": "masculino",
    "ROGER GOMES": "masculino",
    "BEBETO DO RIO SECO": "masculino",
    "PABLO DA AGUA": "masculino",
    "LUCAS MUNIZ": "masculino",
    "GLAUBER POUBEL": "masculino",
    "VINICIUS": "masculino",
    "JALMIR JUNIOR": "masculino",
    "ROMARIO REGIS": "masculino",
    "CLEBER SALAZAR": "masculino",
    "JOAO NUNES": "masculino",
    "DENILSON": "masculino",
    "FRANKLIN DA ESCOLINHA": "masculino",
    "ALFREDO DA CLÍNICA": "masculino",
    "DERLAN RODRIGUES": "masculino",
    "WALDEMIR GOMES": "masculino",
    "ADALTON PANDA": "masculino",
    "MÜLLER SOUZA": "masculino",
    "AMÓS LAURINDO": "masculino",
    "DR RAIMUNDO AMORIM": "masculino",
    # 2020 — confirmados por você
    "GAB GREG": "masculino",
    "PASTOR BRUM": "masculino",
    "CASÉ": "masculino",
    "ARMADINHO PENÉLIS": "masculino",
    "THUIN": "masculino",
    "BOQUINHA": "masculino",
    "QUINZÉ": "masculino",
    "AQUICILEY FILHO ADÃO DO CAMPO": "masculino",
    "ZIEL PAVANI": "masculino",
    "MIGA": "masculino",
    "PROFESSOR JOSIMAR": "masculino",
    "PROFESSOR GUTO GARCIA": "masculino",
    "FAROL DO PAIOL": "masculino",
    "MAURINHO DO PAIOL": "masculino",
    "FOLHA": "masculino",
    "CASOTA": "masculino",
    "DR EMANUEL ROCHA": "masculino",
    "CHICÃO": "masculino",
    "CASOBA DA ACADEMIA": "masculino",
    "DJ DENILSON": "masculino",
    "KAEL": "masculino",
    "DAVI DO ESPORTE AGORA É": "masculino",
    "AMARILDO ORELHA": "masculino",
    "PROF JOSEMAR": "masculino",
    "BEBETO": "masculino",
    "KBÇA": "masculino",
    "TATÃO": "masculino",
    "DIDÊ": "masculino",
    "CHIMBIU": "masculino",
    "TECO DESPACHANTE": "masculino",
    "ADEMIR ENFERMEIRO": "masculino",
}

_MASCULINO = {
    "ABEL", "ABRAÃO", "ABNER", "ACACIO", "ALAN", "ALEX", "ALEXANDRE", "RODRIGO",
    "MARCOS", "MAURICIO", "MAURÍCIO", "MANOEL", "MANINHO", "MARLON", "DOUGLAS",
    "WILSON", "WAINER", "TULIO", "ROBERTINHO", "ALLAN", "SYLVIO", "FABIANO",
    "DENILSO", "JEAN", "AMORIM",
    "ALLEFE", "ALCEMIR", "ANDERSON", "ANDRIGO", "ANDRE", "ANDRÉ", "ANGELO",
    "ARTUR", "BALLIESTER", "BETO", "BINHO", "BRUNINHO", "BRUNO",
    "CAIO", "CAL", "CALÉ", "CABO", "CARLINHO", "CARLINHOS", "CARLOS",
    "CASO", "CASE", "CESAR", "CESINHA", "CHARLES", "CHIQUINHO", "CIRO",
    "CLAUDIO", "CLAUDINEI", "CLAUDINHO", "CLERINHO", "CLOVINHO", "CRISTIANO",
    "DANDINHO", "DANIEL", "DANIELZINHO", "DECO", "DEJORGE", "DELSON",
    "DENIS", "DINEY", "DINEI", "DIEGO", "DJ", "DOCA", "DOUTOR", "DR",
    "DUDU", "DUDINO", "EDINHO", "EDSON", "EDUARDO", "ELIAS", "ELIÁS",
    "ELTON", "ELVES", "ERNANE", "EVERTON", "FÁBIO", "FABINHO", "FABÃO",
    "FABRICIO", "FABRÍCIO", "FELIPE", "FERNANDINHO", "FERNANDO", "FIDEL",
    "FILIPE", "FILIPPE", "FRED", "GABRIEL", "GALLO", "GILMAR", "GIORGIO",
    "GIOVANI", "GREG", "GU", "GUSTAVO", "HAROLDO", "HEBER", "HELINHO",
    "HENRIQUE", "HYGOR", "IGOR", "IGO", "ISAAC", "JACKSON", "JAMES",
    "JAPERI", "JC", "JEFERSON", "JEFFERSON", "JEORDANE", "JORGINHO",
    "JOSE", "JOSÉ", "JOÃO", "JUAN", "JULIO", "JULIANO", "JUNINHO",
    "JUNIOR", "KASSIANO", "KELVEN", "KLÉVIS", "LECINHO", "LEANDRO",
    "LECINHO", "LEO", "LÉO", "LEON", "LEONARDO", "LIOMAR", "LUCIANO",
    "LUIZ", "MAGRÃO", "MAICON", "MARCELL", "MARCELO", "MARCELINHO",
    "MARCIO", "MARCIONE", "MARKINHO", "MARQUINHO", "MATEUS", "MATHEUS",
    "MAURICIO", "MAYCON", "MICHEL", "MILTINHO", "MOACIR", "MOISES",
    "MOISÉS", "MULLER", "NATAN", "NELSINHO", "NEM", "NILDO", "NILDINHO",
    "NILSINHO", "NOEL", "ORLANDO", "OTOJANES", "PASTOR", "PAULINHO",
    "PAULISTA", "PAULO", "PEDRO", "PEDRINHO", "PIERO", "PISSULA",
    "POUBEL", "PROFESSOR", "RAFAEL", "RANGEL", "REGINALDO", "RENATO",
    "RENATINHO", "RIBEIRO", "RICARDO", "ROBERTO", "ROGERIO", "ROGÉRIO",
    "ROGERINHO", "ROMAR", "RONI", "ROQUE", "ROND", "SAMUEL", "SANDRO",
    "SANDRINHO", "SARGENTO", "SERGIO", "SERGINHO", "SIDNEY", "SILVINHO",
    "THIAGO", "THADEU", "THIAGUINHO", "TIAGO", "TICO", "TIKINHO",
    "TOINZINHO", "TUNINHO", "UDSON", "UÁLLAFE", "VALDECY", "VANILDO",
    "VITOR", "VINÍCIUS", "VITINHO", "VAGUINHO", "WALLACE", "WALTER",
    "WANDERSON", "WELINGTON", "WENDELL", "WESLEY", "WILLIAM", "YGOR",
    "ZAF", "ZÉ", "ZEZINHO", "ARMANDINHO", "AMARO", "ALLEFE", "ABNER",
    "TELMINHO", "MAGÚ", "MACREI", "TITI", "CACAU", "NUNA", "MANU",
    "MARVEL", "CHAPINHA", "CATITI", "CAMU", "BAIXINHO", "CABELUDO",
    "AMIGO", "TIÃO", "NANÁ",
}

_FEMININO = {
    "ADRIANA", "ALINE", "ANDREIA", "AMANDA", "BENNY", "CRISTINA", "DELZA",
    "DRA", "DRA.", "DOUTORA", "ERIKA", "ELISIA", "ENFERMEIRA",
    "FERNANDA", "JANE", "JULIANA", "LEANDRA", "LÚ", "MARCELA",
    "MARCIA", "MAYARA", "MISLENE", "MISTRAL", "NANÁ", "PASTORA", "PATRÍCIA",
    "PROFESSORA", "RAYANE", "REGINA", "RENATA", "SORAIA", "SUELY", "THAMIRES",
}


def infer_gender(nome_urna: str) -> str:
    upper = nome_urna.strip().upper()
    if upper in _GENERO_MANUAL:
        return _GENERO_MANUAL[upper]
    tokens = upper.split()
    if not tokens:
        return "indefinido"
    token = tokens[0]
    if token in _TITULOS and len(tokens) > 1:
        token = tokens[1]
    if token in _FEMININO:
        return "feminino"
    if token in _MASCULINO:
        return "masculino"
    return "indefinido"


def slugify_snake(s: str) -> str:
    s = (s or "").strip().upper()
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = re.sub(r"[^A-Z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s.replace(" ", "_")


def parse_float_ptbr(x: Any) -> Optional[float]:
    if x is None:
        return None
    s = str(x).strip()
    if s == "":
        return None
    # tolerar "186.435" (milhar) e "0,0382" (decimal pt-br)
    if "," in s and "." in s:
        # assume . milhar, , decimal
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    return float(s)


def resolve_neighbors_path(target_slug: str) -> str:
    idx = json.load(open(MAP_INDEX, encoding="utf-8"))
    for c in idx.get("counties", []):
        if slugify_snake(c.get("county", "")) == target_slug:
            p = c.get("output")
            if not p or not os.path.exists(p):
                raise FileNotFoundError(f"neighbors_json não encontrado: {p}")
            return p
    raise ValueError(f"Município slug={target_slug} não encontrado no index.json")


def resolve_county_id(target_slug: str) -> int:
    counties = list(County.objects.filter(state__name="RJ").values_list("id", "name"))
    slug_to_id = {slugify_snake(nm): cid for cid, nm in counties}
    cid = slug_to_id.get(target_slug)
    if not cid:
        raise ValueError(f"County.id não encontrado para slug={target_slug}")
    return int(cid)


def resolve_qe(target_slug: str) -> float:
    qe_df = pd.read_csv(QE_CSV, sep=";", encoding="latin-1")
    qe_df = qe_df[(qe_df["UF"] == "RJ") & (qe_df["ds_cargo"] == "Vereador")].copy()
    qe_df["mun_slug"] = qe_df["Município"].map(slugify_snake)
    sub = qe_df[qe_df["mun_slug"] == target_slug]
    if sub.empty:
        raise ValueError(f"QE não encontrado para slug={target_slug}")
    # validar consistência do QE no município
    qes = sorted({int(parse_float_ptbr(v)) for v in sub["vr_quociente_eleitoral"].tolist()})
    if len(qes) > 1:
        raise ValueError(f"QE divergente no município {target_slug}: {qes}")
    return float(qes[0])


def load_eleitos(target_slug: str) -> pd.DataFrame:
    df = pd.read_csv(ELEITOS_CSV, sep=";", encoding="latin-1")
    df = df[
        (df["sg_uf"] == "RJ")
        & (df["ds_cargo"] == "Vereador")
        & (df["ds_sit_totalizacao"] == "Eleito")
        & (df["nr_turno"] == 1)
    ].copy()
    df["mun_slug"] = df["nm_municipio"].map(slugify_snake)
    df = df[df["mun_slug"] == target_slug]
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Fuzzy vereadores eleitos 2020 por município")
    parser.add_argument("--municipio", default="NITERÓI", help="Nome do município (ex.: NITERÓI)")
    args = parser.parse_args()

    target_municipio = args.municipio
    target_slug = slugify_snake(target_municipio)

    neighbors_path = resolve_neighbors_path(target_slug)
    qe = resolve_qe(target_slug)
    county_id = resolve_county_id(target_slug)

    eleitos = load_eleitos(target_slug)
    if eleitos.empty:
        raise SystemExit(f"Nenhum eleito encontrado no CSV para {target_municipio}")

    pols = list(
        Political.objects.filter(
            political_type__name="Vereador",
            election__year=2020,
            region="city",
            region_id=county_id,
        ).select_related("political_party", "election")
    )
    if not pols:
        raise SystemExit("Nenhum Political encontrado no banco para vereador 2020 no município")

    pol_by_full: Dict[str, Political] = {slugify_snake(p.full_name): p for p in pols}
    pol_by_name: Dict[str, Political] = {slugify_snake(p.name): p for p in pols}
    pol_by_code: Dict[int, Political] = {
        int(p.political_code): p for p in pols if p.political_code is not None
    }

    out_rows: List[Dict[str, Any]] = []
    unmatched: List[Dict[str, Any]] = []

    for _, r in eleitos.iterrows():
        nm = str(r["nm_candidato"])
        urna = str(r["nm_urna_candidato"])
        nr = int(r["nr_candidato"])
        partido_csv = str(r["sg_partido"])

        p = pol_by_full.get(slugify_snake(nm))
        if p is None:
            p = pol_by_name.get(slugify_snake(nm))
        if p is None:
            p = pol_by_name.get(slugify_snake(urna))
        if p is None:
            p = pol_by_code.get(nr)

        if p is None:
            unmatched.append(
                {
                    "municipio": target_municipio,
                    "nm_candidato": nm,
                    "nm_urna_candidato": urna,
                    "nr_candidato": nr,
                    "sg_partido": partido_csv,
                }
            )
            continue

        result = analyze_political_concentration(
            political_id=p.id,
            qe=qe,
            neighbors_json_path=neighbors_path,
            output_path=None,
        )

        out_rows.append(
            {
                "municipio": target_municipio,
                "qe": qe,
                "political_id": p.id,
                "candidato": p.name,
                "full_name": p.full_name,
                "partido": partido_csv,
                "genero": infer_gender(urna),
                "total_votes": result["political"]["total_votes"],
                "concentracao_final": result["summary"]["concentracao_final"],
                "interpretation": result["summary"]["interpretation"],
                "total_conglomerates": result["summary"]["total_conglomerates"],
                "municipios_map_file": os.path.basename(neighbors_path),
                "unmatched_in_csv": False,
            }
        )

    results_dir = os.path.join(BASE_DIR, "cartpol_app", "scripts", "conglomerates", "results")
    os.makedirs(results_dir, exist_ok=True)

    out_csv = os.path.join(results_dir, f"test_{target_slug}_vereadores_eleitos_2020.csv")
    unmatched_json = os.path.join(results_dir, f"test_{target_slug}_unmatched_2020.json")

    if out_rows:
        with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
            w.writeheader()
            w.writerows(out_rows)
    else:
        with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
            f.write("no_matches\n")

    with open(unmatched_json, "w", encoding="utf-8") as f:
        json.dump(unmatched, f, ensure_ascii=False, indent=2)

    print(f"Municipio: {target_municipio} (slug={target_slug})")
    print(f"Eleitos CSV: {len(eleitos)}")
    print(f"Matches: {len(out_rows)}")
    print(f"Unmatched: {len(unmatched)}")
    print(f"QE: {qe}")
    print(f"neighbors_json: {neighbors_path}")
    print(f"CSV: {out_csv}")
    print(f"Unmatched JSON: {unmatched_json}")


if __name__ == "__main__":
    main()

