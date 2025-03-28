import csv
import functools
from itertools import batched

import requests

from cartpol_app.scripts.database.helpers import (
    contains_duplicates_political, contains_duplicates_political_party)

CD_CARGO = [11, 13, 6, 7, 5, 1, 3]

#candidato_mun_zona

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


DEZ_PRINCIPAIS_MUN = ['38490', '13897', '25313',
                      '02550', '71072', '41238', '60011', '75353', '88013']

ELETION_CODE = ['220', '426', '546', '297', '619']

headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}

ELECTION_ID = {
    '2016': {
        'id': 4,
        '11': 9,
        '13': 10
    },
    '2018': {
        'id': 3,
        '6': 7,
        '7': 6,
        '5': 8,
        '1': 13,
        '3': 16,
    },
    '2020': {
        'id': 2,
        '11': 4,
        '13': 5
    },
    '2022': {
        'id': 1,
        '6': 2,
        '7': 1,
        '5': 3,
        '1': 14,
        '3': 15,
    },
    '2024': {
        'id': 5,
        '11': 11,
        '13': 12,
    }

}


def post_politics(url, year):

    politics_array = []
    political_party_array = []

    with open(f'data/votacao_candidato_munzona_SP_{year}.csv', 'r', encoding='utf-8') as f:
        print("Começando a selecionar partidos e candidatos")

        reader = csv.reader(f, delimiter=',', strict=True)
        next(reader)

        for row in reader:
            # Removendo votos nulos
            if row[INDEX_CANDIDATE_ID] in ['95', '96'] or row[INDEX_ROUND] != '1':
                continue

            political_dict = {
                "election": ELECTION_ID[str(year)]["id"],
                "name": row[INDEX_NAME].strip(),
                "full_name": row[INDEX_FULL_NAME].strip(),
                "political_party": row[INDEX_POLITICAL_PARTY],
                "political_type": int(row[INDEX_CARGO]),
                "political_id": row[INDEX_CANDIDATE_ID],
                "political_code": row[INDEX_POLITICAL_NUMBER],
                "county_id": row[INDEX_COUNTY_ID],
                "year": year,
                "region": 'city' if row[INDEX_CARGO] in ['13', '11']  else 'state'
            }

            county = request_county(f"{url}county?state={row[INDEX_STATE]}&tse_id={
                                    row[INDEX_COUNTY_ID]}")

            if county is not None:
                political_dict["region_id"] = county
            else:
                continue

            if int(political_dict["political_type"]) in CD_CARGO:
                political_dict["political_type"] = ELECTION_ID[str(
                    year)][row[INDEX_CARGO]]
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
