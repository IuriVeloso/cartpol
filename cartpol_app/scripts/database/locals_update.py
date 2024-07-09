import csv

import requests

from cartpol_app.scripts.database.helpers import (
    contains_duplicates_county, contains_duplicates_electoral_zone,
    contains_duplicates_neighborhood, contains_duplicates_state)

INDEX_SECTION_ID = 6
INDEX_ZONE_ID = 7
INDEX_LOCAL_ID = 11
INDEX_ADDRESS = 3
INDEX_STATE = 2
INDEX_CEP = 5
INDEX_BAIRRO = 4
INDEX_MUNICIPIO = 0
INDEX_MUNICIPIO_ID = 1
CD_CARGO = {
    "prefeito": 11,
    "vereador": 13
}

CD_STATE = {
    "RJ": "Rio de Janeiro",
    "MG": "Minas Gerais",
    "SP": "São Paulo",
    "ES": "Espírito Santo",
}


def locals_update(url):
    print("Começando a selecionar locais de votacao, bairros e secao")

    with open('data/local_votacao_BRASIL.csv', 'r', encoding='utf-8') as f:
        section_array = []
        neighborhood_array = []
        electoral_zones_array = []
        county_array = []
        state_array = []

        reader = csv.reader(f, delimiter=';', strict=True)
        next(reader)

        for row in reader:
            if row[INDEX_STATE] not in CD_STATE:
                continue

            section_dict = {
                "identifier": row[INDEX_SECTION_ID],
                "cep": row[INDEX_CEP],
                "address": str(row[INDEX_ADDRESS]).strip(),
                "electoral_zone": int(row[INDEX_ZONE_ID]),
                "electoral_zone_script_id": int(row[INDEX_ZONE_ID]),
                "neighborhood": row[INDEX_BAIRRO].strip(),
                "county_name": row[INDEX_MUNICIPIO],
                "script_id": row[INDEX_LOCAL_ID],
            }

            state_dict = {"name": row[INDEX_STATE],
                          "full_name": CD_STATE[row[INDEX_STATE]]}
            electoral_zones_dict = {
                "identifier": int(row[INDEX_ZONE_ID]),
                "state": row[INDEX_STATE],
                "county": row[INDEX_MUNICIPIO]}
            county_dict = {
                "name": row[INDEX_MUNICIPIO], "state": row[INDEX_STATE]}
            neighborhood_dict = {
                "name": row[INDEX_BAIRRO].strip(),
                "county_id": row[INDEX_MUNICIPIO_ID],
                "county_name": row[INDEX_MUNICIPIO]}

            section_array.append(section_dict)

            if contains_duplicates_neighborhood(neighborhood_dict, neighborhood_array):
                neighborhood_array.append(neighborhood_dict)

            if contains_duplicates_county(county_dict, county_array):
                county_array.append(county_dict)

            if contains_duplicates_electoral_zone(electoral_zones_dict, electoral_zones_array):
                electoral_zones_array.append(electoral_zones_dict)

            if contains_duplicates_state(state_dict, state_array):
                state_array.append(state_dict)

    print("\nTerminando de selecionar entidades de local, começando a \
        atualizar a base...\n")

    state_array_created = []
    county_array_created = []
    neighborhood_array_created = []
    electoral_zones_array_created = []

    print("\nInserindo estados\n")

    for state in state_array:
        response = requests.post(url + "state", data=state)
        response_json = response.json()
        state_array_created.append(response_json)

    for state in state_array_created:
        def apply_state_id(x):
            if isinstance(x["state"], str) and\
                    str.lower(x["state"]) == str.lower(state["name"]):
                x["state"] = state["id"]
            return x

        county_array_completed = list(map(apply_state_id, county_array))
        electoral_zones_array_completed = list(
            map(apply_state_id, electoral_zones_array))

    print("\nInserindo municipios\n")

    for county in county_array_completed:
        response = requests.post(url + "county", data=county)
        response_json = response.json()
        county_array_created.append(response_json)

    print(county_array_created.__len__(), "municipios criados")

    print("\nMunicipios finalizados. Inserindo zonas eleitorais\n")

    for electoral_zone in electoral_zones_array_completed:
        response = requests.post(url + "electoral-zone/", data=electoral_zone)
        response_json = response.json()
        response_json["county"] = electoral_zone["county"]
        electoral_zones_array_created.append(response_json)

    print(electoral_zones_array_created.__len__(),
          "zonas eleitorais criadas. Selecionando bairros")

    for county in county_array_created:
        def apply_county_id(x):
            if isinstance(x["county_name"], str) and str.lower(x["county_name"]) == str.lower(county["name"]):
                x["county"] = county["id"]
            return x
        neighborhood_array = list(map(apply_county_id, neighborhood_array))

    print("\nInserindo bairros.\n")

    for neighborhood in neighborhood_array:
        response = requests.post(url + "neighborhood/", data=neighborhood)
        response_json = response.json()
        response_json["county_name"] = neighborhood["county_name"]
        neighborhood_array_created.append(response_json)
    print(neighborhood_array_created.__len__(),
          " bairros criados. Selecionando secoes\n")

    print("\n\nInserindo secoes\n")
    
    sections_craeated = 0

    for section in section_array:
        neighborhood = next((obj["id"] for obj in neighborhood_array_created
                             if (str.lower(obj["name"]) == str.lower(section["neighborhood"])) and (obj["county_name"] == section["county_name"])), None)

        electoral_zone = next((obj["id"] for obj in electoral_zones_array_created
                             if (str(section["electoral_zone"]) == obj["identifier"]) and (section["county_name"] == obj["county"])), None)

        if neighborhood is None:
            print("Neighborhood not found " + section["neighborhood"])
            break
        
        if electoral_zone is None:
            print("ZE not found " + str(section["electoral_zone"]))
            break
        

        section["neighborhood"] = neighborhood
        section["electoral_zone"] = electoral_zone
        response = requests.post(url + "section/", data=section)
        
        if response.status_code == 201:
            sections_craeated+=1

    print(str(sections_craeated), "secoes criadas\n")