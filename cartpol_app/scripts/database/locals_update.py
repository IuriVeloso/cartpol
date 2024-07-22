import csv
import functools

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


@functools.lru_cache(maxsize=2048)
def request_county(string):
    resp = requests.get(string).json()
    if len(resp) > 0:
        return resp[0]["id"]
    return None


@functools.lru_cache(maxsize=8192)
def request_neighborhood(string):
    resp = requests.get(string).json()
    if len(resp) > 0:
        return resp[0]["id"]
    return None


@functools.lru_cache(maxsize=2048)
def request_electoral_zone(string):
    resp = requests.get(string).json()
    if len(resp) > 0:
        return resp[0]["id"]
    return None


@functools.lru_cache(maxsize=32)
def request_state(string):
    resp = requests.get(string).json()
    if len(resp) > 0:
        return resp[0]["id"]
    return None


def locals_update(url):
    print("Começando a selecionar locais de votacao, bairros e secao")

    with open('data/local_votacao_BRASIL_2020.csv', 'r', encoding='utf-8') as f:
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

            state, county, zone_id, neighborhood, tse_id = row[INDEX_STATE], row[
                INDEX_MUNICIPIO], row[INDEX_ZONE_ID], row[INDEX_BAIRRO].strip(), row[INDEX_MUNICIPIO_ID]

            section_dict = {
                "identifier": row[INDEX_SECTION_ID],
                "cep": row[INDEX_CEP],
                "address": str(row[INDEX_ADDRESS]).strip(),
                "electoral_zone": zone_id,
                "neighborhood": neighborhood,
                "county_name": county,
                "script_id": row[INDEX_LOCAL_ID],
            }

            state_dict = {"name": state,
                          "full_name": CD_STATE[state]}
            electoral_zones_dict = {
                "identifier": zone_id,
                "state": state,
                "county": county}
            county_dict = {
                "name": county, "state": state, "tse_id": tse_id}
            neighborhood_dict = {
                "name": neighborhood,
                "county_id": tse_id,
                "county_name": county,
                "state": state}

            section_array.append(section_dict)

            if contains_duplicates_state(state, state_array):
                state_array.append(state_dict)

            if contains_duplicates_neighborhood(neighborhood, county, neighborhood_array):
                neighborhood_array.append(neighborhood_dict)

            if contains_duplicates_county(tse_id, county_array):
                county_array.append(county_dict)

            if contains_duplicates_electoral_zone(zone_id, state, county, electoral_zones_array):
                electoral_zones_array.append(electoral_zones_dict)

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

    print("\nInserindo municipios\n")

    for county in county_array:
        state_id = request_state(f"{url}state?name="
                                 + county["state"])

        if state_id is not None:
            county["state"] = state_id
        else:
            print("StateNotFound")
            print(county)
            raise Exception("StateNotFound")
        response = requests.post(url + "county", data=county)
        response_json = response.json()
        county_array_created.append(response_json)
    request_state.cache_clear()

    print(county_array_created.__len__(), "municipios criados")

    print("\nMunicipios finalizados. Inserindo zonas eleitorais\n")

    for electoral_zone in electoral_zones_array:
        search_url = (f"{url}county?name={electoral_zone['county']}" +
                      f"&state={electoral_zone['state']}")
        county_id = request_county(search_url)

        if state_id is not None:
            electoral_zone["county"] = county_id
        else:
            print("CountyNotFound")
            print(electoral_zone)
            raise Exception("CountyNotFound")

        response = requests.post(url + "electoral-zone/", data=electoral_zone)
        response_json = response.json()
        electoral_zones_array_created.append(response_json)

    print(electoral_zones_array_created.__len__(),
          "zonas eleitorais criadas. Selecionando bairros")

    for neighborhood in neighborhood_array:
        county_id = request_county(f"{url}county?state="
                                   + neighborhood["state"]
                                   + "&name="
                                   + neighborhood["county_name"])

        if county_id is not None:
            neighborhood["county"] = county_id
        else:
            print("CountyNotFound")
            print(neighborhood)
            raise Exception("CountyNotFound")
    request_county.cache_clear()

    print("\nInserindo bairros.\n")

    for neighborhood in neighborhood_array:
        response = requests.post(url + "neighborhood/", data=neighborhood)
        response_json = response.json()
        neighborhood_array_created.append(response_json)
    print(neighborhood_array_created.__len__(),
          " bairros criados. Selecionando secoes\n")

    sections_created = 0

    for section in section_array:
        neighborhood_id = request_neighborhood(f"{url}neighborhood?county="
                                               + section["county_name"]
                                               + "&name="
                                               + section["neighborhood"])

        electoral_zone_id = request_electoral_zone(f"{url}electoral-zone?county="
                                                   + section["county_name"]
                                                   + "&identifier="
                                                   + section["electoral_zone"])

        if neighborhood_id is not None and electoral_zone_id is not None:
            section["neighborhood"] = neighborhood_id
            section["electoral_zone"] = electoral_zone_id
        else:
            print("NeighborhoodNotFound")
            print(section)
            raise Exception("NeighborhoodNotFound")
    request_neighborhood.cache_clear()
    request_electoral_zone.cache_clear()

    print("\n\nInserindo secoes\n")

    for section in section_array:
        response = requests.post(url + "section/", data=section)
        if response.status_code == 201:
            sections_created += 1
        else:
            print(section)
            print(response.json())

    print(str(sections_created), "secoes criadas\n")
