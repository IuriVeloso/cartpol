import csv

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
INDEX_ZONE_ID = 15
INDEX_ADDRESS = 25
CD_CARGO = {
    "prefeito": 11,
    "vereador": 13
}


def post_votes(url, politics_array_created, section_array_created):
    votes_array = []

    with open('data/votacao_secao_2020_RJ.csv', 'r', encoding='utf-8') as f:
        print("Começando a selecionar votos")

        reader = csv.reader(f, delimiter=';', strict=True)
        errors = 0

        next(reader)

        for row in reader:

            if row[INDEX_CANDIDATE_ID] in ['95', '96']:
                continue

            votes_dict = {
                "quantity": row[INDEX_VOTES],
                "description": row[INDEX_VOTES] + " votos para "
                + row[INDEX_NAME],
                "political_id": row[INDEX_CANDIDATE_ID],
                "section_id": str.lower(str(row[INDEX_ZONE_ID])
                                        + '-' +
                                        str(row[INDEX_SECTION_ID]) + '-'
                                        + str(row[INDEX_ADDRESS]))
                .replace(" ", ""),
                "county_id": row[INDEX_COUNTY_ID],
                "zone_id": row[INDEX_ZONE_ID],
            }

            if ((int(row[INDEX_CARGO]) == CD_CARGO["prefeito"]
                 and row[INDEX_ELECTION_CODE] == "426"
                 and row[INDEX_ROUND] == "1")
                or
                    (int(row[INDEX_CARGO]) == CD_CARGO["vereador"]
                     and row[INDEX_ELECTION_CODE] == "426"
                     and row[INDEX_ROUND] == "1"
                     and len(row[INDEX_CANDIDATE_ID]) > 3)):
                votes_dict["political"] = next((political["id"] for political
                                                in politics_array_created
                                                if str.lower(
                    political["political_script_id"]) ==
                    votes_dict["political_id"]), None)

                votes_dict["section"] = next((section["id"] for section
                                              in section_array_created
                                              if section["section_script_id"]
                                              == votes_dict["section_id"]),
                                             None)

                if (votes_dict["political"] is None or
                        votes_dict["section"] is None):
                    print("Erro nos votos")
                    print(votes_dict)
                    errors += 1
                    continue
                votes_array.append(votes_dict)

    print("Terminando de selecionar votos\n")
    print(votes_array.__len__())

    votes_array_created = []
    votes_index = 0

    print("Inserindo votos\n")

    for votes in votes_array:
        votes_index += 1
        if votes_index % 20000 == 0:
            print(
                f'{round(votes_index/votes_array.__len__(), 2)}% politicos inseridos')

        response = requests.post(url + "votes/", data=votes)
        response_json = response.json()
        votes_array_created.append(response_json)

    print(votes_array_created.__len__(), "votos criados")
    print("\nVotos finalizados\n")
    print(f'{errors} votos falharam em ser criados\n')
