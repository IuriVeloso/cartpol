import csv

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


def post_politics(url):
    politics_array = []
    political_party_array = []

    with open('data/votacao_candidato_munzona_2020_BRASIL.csv', 'r', encoding='latin-1') as f:
        print("Começando a selecionar partidos e candidatos")

        reader = csv.reader(f, delimiter=';', strict=True)
        county = [{"name": 0}]

        next(reader)

        for row in reader:
            # Removendo votos nulos e restringindo ao sudeste
            if row[INDEX_CANDIDATE_ID] in ['95', '96'] or row[INDEX_STATE] not in ['RJ', 'MG', 'SP', 'ES'] or row[INDEX_ROUND] != '1' or row[INDEX_ELECTION_CODE] != '426':
                continue
            political_dict = {
                "election": 1,
                "name": row[INDEX_NAME],
                "full_name": row[INDEX_FULL_NAME],
                "political_party": row[INDEX_POLITICAL_PARTY],
                "political_type": row[INDEX_CARGO],
                "county_name": str.lower(row[INDEX_COUNTY]).replace(" ", ""),
                "political_id": row[INDEX_CANDIDATE_ID],
                "political_script_id": row[INDEX_POLITICAL_NUMBER],
                "region": 'city'
            }

            if len(county) != 0 and county[0]["name"] != row[INDEX_COUNTY] or len(county) == 0:
                county = requests.get(
                    f"{url}county?state={row[INDEX_STATE]}&name={row[INDEX_COUNTY]}").json()

            if len(county) != 0:
                political_dict["region_id"] = county[0]["id"]

            if int(political_dict["political_type"]) == CD_CARGO["prefeito"]:
                political_dict["political_type"] = 1
                if contains_duplicates_political(political_dict, politics_array):
                    politics_array.append(political_dict)

                if contains_duplicates_political_party(political_dict, political_party_array):
                    political_party_dict = {
                        "name": row[INDEX_POLITICAL_PARTY],
                        "full_name": row[INDEX_POLITICAL_PARTY_FULL_NAME],
                        "active": True
                    }
                    political_party_array.append(political_party_dict)
            if int(political_dict["political_type"]) == CD_CARGO["vereador"]:
                political_dict["political_type"] = 2
                if political_dict["political_id"].__len__() < 4:
                    continue
                if contains_duplicates_political(political_dict, politics_array):
                    politics_array.append(political_dict)

                if contains_duplicates_political_party(political_dict, political_party_array):
                    political_party_dict = {
                        "name": row[INDEX_POLITICAL_PARTY],
                        "full_name": row[INDEX_POLITICAL_PARTY_FULL_NAME],
                        "active": True
                    }
                    political_party_array.append(political_party_dict)

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

    print(political_party_array_created.__len__(), "partidos criados")
    print("\n\nPartidos finalizados. Inserindo politicos\n")

    politics_index = 0

    for political_party in political_party_array_created:
        def apply_political_party_id(x):
            if isinstance(x["political_party"], str) and x["political_party"] == political_party["name"]:
                x["political_party"] = political_party["id"]
            return x

        politics_array = list(map(apply_political_party_id, politics_array))

    for politics in politics_array:
        politics_index += 1
        if politics_index % 20000 == 0:
            print(
                f'{round(politics_index*100/politics_array.__len__(), 2)}% politicos inseridos')

        response = requests.post(url + "political/", data=politics)
        if response.status_code == 201:
            response_json = response.json()
            response_json["political_script_id"] = politics["political_script_id"]
            politics_array_created.append(response_json)

    print(politics_array_created.__len__(), "politicos criados")

    return politics_array_created
