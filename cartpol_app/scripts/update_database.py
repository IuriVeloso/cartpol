import csv
import datetime
import requests
from cartpol_app.scripts.base_info import base_info
from cartpol_app.scripts.locals_update import locals_update
from cartpol_app.scripts.politics_update import post_politics
from cartpol_app.scripts.helpers import contains_duplicates_political, contains_duplicates_political_party

URL = "http://127.0.0.1:8000/cartpol/"

INDEX_CARGO = 17
INDEX_ZONA = 15
INDEX_NAME = 20
INDEX_FULL_NAME = 20
INDEX_CANDIDATE_ID = 19
INDEX_POLITICAL_PARTY = 0
INDEX_POLITICAL_PARTY_FULL_NAME = 0
INDEX_VOTES = 21
INDEX_ELECTION_CODE = 6
INDEX_ROUND = 5
INDEX_COUNTY = 14
CD_CARGO = {
    "prefeito": 11,
    "vereador": 13
} 

def post_counties():

    politics_array = []
    political_party_array = []
    votes_array = []
    
    with open('data/votacao_secao_2020_RJ.csv', 'r', encoding='latin-1') as f:
        print("Começando a selecionar zonas eleitorais e municipios")
        
        reader = csv.reader(f, delimiter=';', strict=True)

        next(reader)

        for row in reader:
            votes_dict = {
                "quantity": row[INDEX_VOTES],
                "description": row[INDEX_VOTES] + " votos para " + row[INDEX_NAME],
                "political_full_name": row[INDEX_FULL_NAME],
                "political_id": row[INDEX_CANDIDATE_ID],
                "section_id": int(row[INDEX_ZONA])
            }
                
            if int(row[INDEX_CARGO]) == CD_CARGO["prefeito"] and row[INDEX_ELECTION_CODE] == "426" and row[INDEX_ROUND] == "1":
                votes_array.append(votes_dict)
                    
            if int(row[INDEX_CARGO]) == CD_CARGO["vereador"] and row[INDEX_ELECTION_CODE] == "426" and row[INDEX_ROUND] == "1":
                votes_array.append(votes_dict)

    
    print("Terminando de selecionar candidatos\n\n")
    print(politics_array.__len__())
    print("\n\n")
    
    print("Terminando de selecionar partidos\n\n")
    print(political_party_array.__len__())
    print("\n\n")
    
    print("Terminando de selecionar votos\n\n")
    print(votes_array.__len__())
    print("\n\n")
        
    votes_array_created = []

    
    # print("\n\nInserindo votos\n")

    # for votes in votes_array:
    # political = next((obj for obj in politics_array_created 
    # if str.lower(obj["political_scriptId"]) == str.lower(votes["political_id"]))
    # , None)
    # zone = next((obj for obj in electoral_zones_array_created
    # if int(obj["identifier"]) == votes["zone_id"])
    # , None)  

    # if political is not None:
    # votes["political"] = political["id"]
    # else:
    # print(votes.__str__())
    # print("Political not found")
    # break

    # if zone is not None:
    # votes["zone"] = zone["id"]
    # else:
    # print("Zone not found")
    # break

    # response = requests.post(URL + "votes/", data=votes)
    # response_json = response.json()
    # votes_array_created.append(response_json)

    # print(votes_array_created.__len__(), "votos criados")



    # print("\n\nInserindo bairros\n")
    



startTime = datetime.datetime.now()
print("\nStarted script running\n")
                    
base_info()

print("\nFinished base info\n")

print("\nStarted updating localization information\n")
                    
county_array_created = locals_update()

print("\nFinished updating localization\n")

print("\nStarted creating politicals\n")

post_politics(county_array_created=county_array_created)

# post_counties()

# print("\nFinished creating politicals and votes\n")

print(f"\nFinished script running\nTotal time: {datetime.datetime.now() - startTime}\n")

#python3 manage.py shell < cartpol_app/scripts/update_database.py