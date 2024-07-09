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
INDEX_COUNTY_NAME = 14
INDEX_ZONE_ID = 15
INDEX_ADDRESS = 25
CD_CARGO = {
    "prefeito": 11,
    "vereador": 13
}


def post_votes(url):
    votes_array = []

    with open('data/votacao_secao_2020_RJ.csv', 'r', encoding='utf-8') as f:
        print("Começando a selecionar votos")

        reader = csv.reader(f, delimiter=';', strict=True)
        errors = 0
        
        political = []
        section = []

        next(reader)

        for row in reader:

            if row[INDEX_CANDIDATE_ID] in ['95', '96']:
                continue

            votes_dict = {
                "quantity": row[INDEX_VOTES],
                "description": row[INDEX_VOTES] + " votos para "
                + row[INDEX_NAME],
                "political_id": row[INDEX_CANDIDATE_ID],
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
                
                
                if len(political) != 0 and political[0]["political_code"] != row[INDEX_CANDIDATE_ID] or len(political) == 0:
                    political = requests.get(
                        f"{url}political/?political_code={row[INDEX_CANDIDATE_ID]}&full_name={row[INDEX_NAME]}").json()

                if len(political) != 0:
                    votes_dict["political"] = political[0]["id"]
                else:
                    votes_dict["political"] = None
                    
                if len(section) != 0 and section[0]["identifier"] != row[INDEX_SECTION_ID] and section[0]["address"] != row[INDEX_ADDRESS] or len(section) == 0:
                    section = requests.get(
                        f"{url}section/?identifier={row[INDEX_SECTION_ID]}&electoral_zone={row[INDEX_ZONE_ID]}&county={row[INDEX_COUNTY_NAME]}").json()

                if len(section) != 0:
                    votes_dict["section"] = section[0]["id"]
                else:
                    votes_dict["section"] = None
                    print("Erro na secao e foda")
                    print(votes_dict)
                    raise Exception("Na traaaave!!!") 

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
