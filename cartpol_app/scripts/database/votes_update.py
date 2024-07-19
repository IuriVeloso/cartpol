import csv
import functools
from itertools import batched

import requests

INDEX_CARGO = 17
INDEX_SECTION_ID = 16
INDEX_NAME = 20
INDEX_FULL_NAME = 20
INDEX_CANDIDATE_ID = 19
INDEX_VOTES = 21
INDEX_ELECTION_CODE = 6
INDEX_ROUND = 5
INDEX_COUNTY_ID = 13
INDEX_COUNTY_NAME = 14
INDEX_ZONE_ID = 15
INDEX_ADDRESS = 25
CD_CARGO = {
    "prefeito": 11,
    "vereador": 13
}


@functools.lru_cache(maxsize=8192)
def request_section(string):
    resp = requests.get(string).json()
    if len(resp) > 0:
        return resp[0]["id"]
    return None


@functools.lru_cache(maxsize=8192)
def request_political(string):
    resp = requests.get(string).json()
    if len(resp) > 0:
        return resp[0]["id"]
    return None


headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}


def post_votes(url):
    votes_array = []

    with open('data/votacao_secao_2020_SUDESTE.csv', 'r', encoding='utf-8') as f:
        print("Começando a selecionar votos")

        reader = csv.reader(f, delimiter=';', strict=True)
        errors = 0

        next(reader)

        for row in reader:

            if row[INDEX_CANDIDATE_ID] in ['95', '96'] or row[INDEX_ROUND] != "1" or row[INDEX_ELECTION_CODE] != '426':
                continue

            votes, name, candidate_id, county_id, county_name, zone_id, section_id, cargo = row[INDEX_VOTES], row[INDEX_NAME], row[
                INDEX_CANDIDATE_ID], row[INDEX_COUNTY_ID], row[INDEX_COUNTY_NAME], row[INDEX_ZONE_ID], row[INDEX_SECTION_ID], row[INDEX_CARGO]

            votes_dict = {
                "quantity": votes,
                "description": " ".join([votes, "votos para", name]),
                "political_id": candidate_id,
                "county_id": county_id,
                "zone_id": zone_id,
            }

            if ((int(cargo) == CD_CARGO["prefeito"])
                or
                (int(cargo) == CD_CARGO["vereador"]
                    and len(candidate_id) > 3)):

                political = request_political(
                    f"{url}political?political_code={candidate_id}&full_name={name}")

                if political is not None:
                    votes_dict["political"] = political
                else:
                    print("Erro achando politico")
                    print(votes_dict)
                    errors += 1
                    continue

                section = request_section(
                    f"{url}section?identifier={section_id}&electoral_zone={zone_id}&county_tse_id={county_id}")

                if section is not None:
                    votes_dict["section"] = section
                else:
                    print("Erro na secao e foda")
                    print(votes_dict)
                    raise Exception("Na traaaave!!!")

                votes_array.append(votes_dict)

    request_political.cache_clear()
    request_section.cache_clear()

    print("Terminando de selecionar votos\n")
    print(len(votes_array))

    votes_index = 0
    votes_created_index = 0

    print("Inserindo votos\n")

    for votes in batched(votes_array, 10):
        votes_index += 10
        votes_list = list(votes)
        if votes_index % 50000 == 0:
            print(
                f'{round(votes_index*100/votes_array.__len__(), 2)}% votos criados')

        response = requests.post(
            url + "votes/", json=votes_list, headers=headers)

        if response.status_code == 201:
            votes_created_index += 10
        else:
            print(response.json())
            for individual_batch in votes_list:
                response = requests.post(
                    f"{url}political/", data=individual_batch, headers=headers)
                if response.status_code == 201:
                    votes_created_index += 1
                else:
                    print(response.json())

    print(votes_created_index, "votos criados")
    print("\nVotos finalizados\n")
    print(f'{errors} votos falharam em ser criados\n')
