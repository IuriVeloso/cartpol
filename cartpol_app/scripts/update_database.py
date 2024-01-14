import csv
import datetime
import requests
from cartpol_app.scripts.base_info import base_info
from cartpol_app.scripts.locals_update import locals_update
from cartpol_app.scripts.helpers import contains_duplicates_political, contains_duplicates_political_party

URL = "http://127.0.0.1:8000/cartpol/"

INDEX_CARGO = 18
INDEX_ZONA = 15
INDEX_NAME = 20
INDEX_FULL_NAME = 20
INDEX_CANDIDATE_ID = 19
INDEX_POLITICAL_PARTY = 0
INDEX_POLITICAL_PARTY_FULL_NAME = 0
INDEX_VOTES = 21
INDEX_ELECTION_CODE = 6
INDEX_ROUND = 5
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
            name = row[14]
            political_dict = {
                "election": 1, 
                "name": row[INDEX_NAME], 
                "full_name": row[INDEX_FULL_NAME], 
                "political_party": row[INDEX_POLITICAL_PARTY], 
                "political_type": row[INDEX_CARGO],
                "county_name": name,
                "political_id": row[INDEX_CANDIDATE_ID],
                }
            
            votes_dict = {
                "quantity": row[INDEX_VOTES],
                "description": row[INDEX_VOTES] + " votos para " + row[INDEX_NAME],
                "political_full_name": row[INDEX_FULL_NAME],
                "political_id": row[INDEX_CANDIDATE_ID],
                "section_id": int(row[INDEX_ZONA])
            }

                
            if int(political_dict["political_type"]) == CD_CARGO["prefeito"] and row[INDEX_ELECTION_CODE] == "426" and row[INDEX_ROUND] == "1":
                votes_array.append(votes_dict)

                if contains_duplicates_political(political_dict, politics_array):
                    politics_array.append(political_dict)
                    
                if contains_duplicates_political_party(political_dict, political_party_array):
                    political_party_dict = {
                        "name": row[INDEX_POLITICAL_PARTY], 
                        "full_name": row[INDEX_POLITICAL_PARTY_FULL_NAME], 
                        "active": True
                        }
                    political_party_array.append(political_party_dict)
                    
            if int(political_dict["political_type"]) == CD_CARGO["vereador"] and row[INDEX_ELECTION_CODE] == "426" and row[INDEX_ROUND] == "1":
                votes_array.append(votes_dict)

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
    print("\n\n")
    
    print("Terminando de selecionar partidos\n\n")
    print(political_party_array.__len__())
    print("\n\n")
    
    print("Terminando de selecionar votos\n\n")
    print(votes_array.__len__())
    print("\n\n")
        
    county_array_created = []
    politics_array_created = []
    political_party_array_created = []
    votes_array_created = []

    
    print("\n\nInserindo partidos\n")
    
    for political_party in political_party_array:
        
        response = requests.post(URL + "political-party/", data=political_party)
        response_json = response.json()
        political_party_array_created.append(response_json)
        
    print(political_party_array_created.__len__(), "partidos criados")
        
        
    print("\n\nInserindo politicos\n")    
    for politics in politics_array:
        political_party = next((obj for obj in political_party_array_created 
                                if obj["name"] == politics["political_party"])
                               , None)
        
        county = next((obj for obj in county_array_created
                       if obj["name"] == politics["county_name"]), None)
        
        if political_party is not None:
            politics["political_party"] = political_party["id"]
        else:
            print("Political party not found")
            break
        
        if politics["political_type"] == CD_CARGO["prefeito"]:
            politics["political_type"] = 1
        else:
            politics["political_type"] = 2
        politics["election"] = 1
        politics["region"] = "city"
        politics["region_id"] = county["id"]
        
        
        response = requests.post(URL + "political/", data=politics)
        response_json = response.json()
        response_json["political_scriptId"] = politics["political_id"]
        politics_array_created.append(response_json)
    
    print(politics_array_created.__len__(), "politicos criados")
    



startTime = datetime.datetime.now()
print("\nStarted script running\n")
                    
base_info()

print("\nFinished base info\n")

print("\nStarted updating localization information\n")
                    
locals_update()

print("\nFinished updating localization\n")

# print("\nStarted creating politicals and votes\n")

# post_counties()

# print("\nFinished creating politicals and votes\n")

print(f"\nFinished script running\nTotal time: {datetime.datetime.now() - startTime}\n")

#python3 manage.py shell < cartpol_app/scripts/update_database.py