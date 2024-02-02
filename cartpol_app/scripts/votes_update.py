import requests, csv

URL = "http://127.0.0.1:8000/cartpol/"

INDEX_CARGO = 17
INDEX_SECTION_ID = 22
INDEX_NAME = 20
INDEX_FULL_NAME = 20
INDEX_CANDIDATE_ID = 19
INDEX_VOTES = 21
INDEX_ELECTION_CODE = 6
INDEX_ROUND = 5
INDEX_COUNTY_ID = 13
CD_CARGO = {
    "prefeito": 11,
    "vereador": 13
} 

def post_votes(politics_array_created, section_array_created):
    votes_array = []
    
    with open('data/votacao_secao_2020_RJ.csv', 'r', encoding='latin-1') as f:
        print("Começando a selecionar votos")
        
        reader = csv.reader(f, delimiter=';', strict=True)

        next(reader)

        for row in reader:
            votes_dict = {
                "quantity": row[INDEX_VOTES],
                "description": row[INDEX_VOTES] + " votos para " + row[INDEX_NAME],
                "political_id": row[INDEX_CANDIDATE_ID],
                "section_id": int(row[INDEX_SECTION_ID]),
                "county_id": row[INDEX_COUNTY_ID],
            }
                
            if int(row[INDEX_CARGO]) == CD_CARGO["prefeito"] and row[INDEX_ELECTION_CODE] == "426" and row[INDEX_ROUND] == "1":
                votes_array.append(votes_dict)
                    
            if int(row[INDEX_CARGO]) == CD_CARGO["vereador"] and row[INDEX_ELECTION_CODE] == "426" and row[INDEX_ROUND] == "1":
                votes_array.append(votes_dict)

    
    print("Terminando de selecionar votos\n\n")
    print(votes_array.__len__())

    votes_array_created = []
    errors = 0
    print("\n\nInserindo votos\n")

    for votes in votes_array:
        if(votes["political_id"] in ['19', '20', '25', '77', '18', '90', '40', '36', '23', '22', '95', '96']):
            continue
        political = next((obj for obj in politics_array_created 
            if (str.lower(obj["political_script_id"]) == str.lower(votes["political_id"]) 
                and obj["county_id"] == votes["county_id"]))
        , None)
    
        section = next((obj for obj in section_array_created
            if int(obj["section_script_id"]) == votes["section_id"])
            , None)  

        if political is not None:
            votes["political"] = political["id"]
        else:
            print(votes.__str__())
            print("Political not found")
            errors += 1
            continue

        if section is not None:
            votes["section"] = section["id"]
        else:
            print(votes.__str__())
            print("Zone not found")
            errors += 1
            continue

        response = requests.post(URL + "votes/", data=votes)
        response_json = response.json()
        votes_array_created.append(response_json)

    print(votes_array_created.__len__(), "votos criados")
    print("\nVotos finalizados\n")
    print(f'{errors} votos falharam em ser criados\n')
