import csv
import functools
from itertools import batched

import requests

from cartpol_app.scripts.database.helpers import (
    contains_duplicates_political, contains_duplicates_political_party)

CD_CARGO = {
    "prefeito": 11,
    "vereador": 13
}

INDEX_CARGO = 16
INDEX_NAME = 21
INDEX_FULL_NAME = 20
INDEX_CANDIDATE_ID = 18
INDEX_POLITICAL_PARTY = 29
INDEX_POLITICAL_PARTY_FULL_NAME = 30
INDEX_ELECTION_CODE = 6
INDEX_ROUND = 5
INDEX_COUNTY = 14
INDEX_COUNTY_ID = 13
INDEX_STATE = 10
INDEX_POLITICAL_NUMBER = 19


@functools.lru_cache(maxsize=2048)
def request_county(string):
    resp = requests.get(string).json()
    if len(resp) > 0:
        return resp[0]["id"]
    return None


@functools.lru_cache(maxsize=64)
def request_political_party(string):
    resp = requests.get(string).json()
    if len(resp) > 0:
        return resp[0]["id"]
    return None


headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}


def post_politics(url):
    politics_array = []
    political_party_array = []

    with open('data/votacao_candidato_munzona_2020_BRASIL.csv', 'r', encoding='latin-1') as f:
        print("Começando a selecionar partidos e candidatos")

        reader = csv.reader(f, delimiter=';', strict=True)
        next(reader)

        for row in reader:
            # Removendo votos nulos e restringindo ao sudeste
            if row[INDEX_CANDIDATE_ID] in ['95', '96'] or row[INDEX_ROUND] != '1' or row[INDEX_ELECTION_CODE] != '426':
                continue

            political_dict = {
                "election": 1,
                "name": row[INDEX_NAME],
                "full_name": row[INDEX_FULL_NAME],
                "political_party": row[INDEX_POLITICAL_PARTY],
                "political_type": int(row[INDEX_CARGO]),
                "political_id": row[INDEX_CANDIDATE_ID],
                "political_code": row[INDEX_POLITICAL_NUMBER],
                "county_id": row[INDEX_COUNTY_ID],
                "region": 'city'
            }

            county = request_county(f"{url}county?state={row[INDEX_STATE]}&tse_id={
                                    row[INDEX_COUNTY_ID]}")

            if county is not None:
                political_dict["region_id"] = county

            if int(political_dict["political_type"]) == CD_CARGO["prefeito"] or (int(political_dict["political_type"]) == CD_CARGO["vereador"] and len(political_dict["political_id"]) > 4):
                political_dict["political_type"] = 1 if political_dict["political_type"] == CD_CARGO["prefeito"] else 2
                if contains_duplicates_political(political_dict, politics_array):
                    politics_array.append(political_dict)

                if contains_duplicates_political_party(political_dict["political_party"], political_party_array):
                    political_party_dict = {
                        "name": row[INDEX_POLITICAL_PARTY],
                        "full_name": row[INDEX_POLITICAL_PARTY_FULL_NAME],
                        "active": True
                    }
                    political_party_array.append(political_party_dict)

    request_county.cache_clear()

    print("Terminando de selecionar candidatos\n\n")
    print(politics_array.__len__())
    print("\nTerminando de selecionar partidos\n\n")
    print(political_party_array.__len__())

    politics_array_created = []
    political_party_array_created = []

    print("\n\nInserindo partidos\n")

    for political_party in political_party_array:

        response = requests.post(
            url + "political-party/", data=political_party)
        response_json = response.json()
        political_party_array_created.append(response_json)

    print(len(political_party_array_created), "partidos criados")

    for politics in politics_array:
        political_party_id = request_political_party(
            f"{url}political-party?name=" + politics["political_party"])

        if political_party_id is not None:
            politics["political_party"] = political_party_id
        else:
            print("PoliticalPartyNotFound")
            print(political_party)
            raise Exception("PoliticalPartyNotFound")
    request_political_party.cache_clear()

    politics_index = 0
    politics_created_index = 0

    print("\n\nPartidos finalizados. Inserindo politicos\n")

    for politics in batched(politics_array, 10):
        politics_index += 1
        if politics_index % 20000 == 0:
            print(
                f'{round(politics_index*100/len(politics_array), 2)}% politicos inseridos')
        list_politics = list(politics)
        response = requests.post(
            f"{url}political/", json=list_politics, headers=headers)
        if response.status_code == 201:
            politics_created_index += 10
        else:
            print(response.json())
            for individual_batch in list_politics:
                response = requests.post(
                    f"{url}political/", data=individual_batch, headers=headers)
                if response.status_code == 201:
                    politics_created_index += 1
                else:
                    print(response.json())

    print(politics_created_index, " politicos criados")

    return politics_array_created
