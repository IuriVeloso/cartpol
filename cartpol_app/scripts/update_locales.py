import csv
import json
import requests

URL = "http://127.0.0.1:8000/cartpol/"

INDEX_CARGO = 16
INDEX_ZONA = 15
INDEX_NAME = 21
INDEX_FULL_NAME = 20
INDEX_POLITICAL_PARTY = 29
INDEX_POLITICAL_PARTY_FULL_NAME = 30
INDEX_VOTES = 41
INDEX_ELECTION_CODE = 6
INDEX_ROUND = 5
CD_CARGO = {
    "prefeito": 11,
    "vereador": 13
}

def contains_duplicates_neighborhood(neighborhood_zone, neighborhood_array):
    result = True
    for neighborhood_object in neighborhood_array:
        if neighborhood_object["name"] == neighborhood_zone["name"] and neighborhood_object["county_name"] == neighborhood_zone["county_name"]:
            result = False
            break
    return result

def contains_duplicates_county(electoral_zone, county_array):
    result = True
    for county_object in county_array:
        if county_object["name"] == electoral_zone["county_name"]:
            result = False
            break
    return result

def contains_duplicates_electoral_zone(electoral_zone, electoral_zone_array):
    result = True
    for electoral_zone_obj in electoral_zone_array:
        if electoral_zone["zone_id"] == electoral_zone_obj["zone_id"]:
            result = False
            break
    return result

def contains_duplicates_political(political, political_array):
    result = True
    for political_obj in political_array:
        if political["name"] == political_obj["name"]:
            result = False
            break
    return result

def contains_duplicates_political_party(political_party, political_party_array):
    result = True
    for political_party_obj in political_party_array:
        if political_party["political_party"] == political_party_obj["name"]:
            result = False
            break
    return result

def base_info():
    election = {'year': 2020, 'round': 1, 'code': 426}
    politicalType = {'name': "Prefeito", 'description': "Deve representar o município nas suas relações jurídicas, políticas e administrativas, além de sancionar, promulgar e publicar as leis"}
    state = {'name': 'RJ', 'full_name': 'Rio de Janeiro'}
    
    response = requests.post(URL + "political-type/", data=politicalType)
    response_json = response.json()
    print("\nPrefeito criado:")
    print(response_json)
    
    response_election = requests.post(URL + "election/", data=election)
    response_election_json = response_election.json()
    print("\nEleicao criada:")
    print(response_election_json)
    
    response_state = requests.post(URL + "state/", data=state)
    response_state_json = response_state.json()
    print("\nEstado criado:")
    print(response_state_json)
    

def post_counties():
    county_array = []
    electoral_zones_array = []
    politics_array = []
    political_party_array = []
    votes_array = []
    
    with open('data/votacao_candidato_munzona_2020_RJ.csv', 'r', encoding='latin-1') as f:
        print("Começando a selecionar zonas eleitorais e municipios")
        
        reader = csv.reader(f, delimiter=';', strict=True)

        next(reader)

        for row in reader:
            name = row[14]
            electoral_zones_dict = {"county_name": name, "state": 1, "zone_id": int(row[INDEX_ZONA])}
            mayor_dict = {
                "election": 1, 
                "name": row[INDEX_NAME], 
                "full_name": row[INDEX_FULL_NAME], 
                "political_party": row[INDEX_POLITICAL_PARTY], 
                "political_type": row[INDEX_CARGO],
                "county_name": name
                }
            
            votes_dict = {
                "quantity": row[INDEX_VOTES],
                "description": row[INDEX_VOTES] + " votos para " + row[INDEX_NAME],
                "political_full_name": row[INDEX_FULL_NAME],
                "zone_id": int(row[INDEX_ZONA])
            }
            
            if contains_duplicates_electoral_zone(electoral_zones_dict, electoral_zones_array):
                electoral_zones_array.append(electoral_zones_dict)

            if contains_duplicates_county(electoral_zones_dict, county_array):
                county_dict = {"name": name, "state": 1}
                county_array.append(county_dict)
                
            if int(mayor_dict["political_type"]) == CD_CARGO["prefeito"] and row[INDEX_ELECTION_CODE] == "426" and row[INDEX_ROUND] == "1":
                votes_array.append(votes_dict)

                if contains_duplicates_political(mayor_dict, politics_array):
                    politics_array.append(mayor_dict)
                    
                if contains_duplicates_political_party(mayor_dict, political_party_array):
                    political_party_dict = {
                        "name": row[INDEX_POLITICAL_PARTY], 
                        "full_name": row[INDEX_POLITICAL_PARTY_FULL_NAME], 
                        "active": True
                        }
                    political_party_array.append(political_party_dict)
        

    print("Terminando de selecionar zone ids\n\n")
    print(electoral_zones_array.__len__())
    print("\n\n")
            
    print("Terminando de selecionar municipios\n\n")
    print(county_array.__len__())
    print("\n\n")
    
    print("Terminando de selecionar candidatos\n\n")
    print(politics_array.__len__())
    print("\n\n")
    
    print("Terminando de selecionar partidos\n\n")
    print(political_party_array.__len__())
    print("\n\n")
    
    print("Terminando de selecionar votos\n\n")
    print(votes_array.__len__())
    print("\n\n")
            
    with open('data/lista_zonas_eleitorais.csv', 'r', encoding='latin-1') as f:        
        electoral_zone_complete = []
        neighborhood_array = []
        
        reader = csv.reader(f)
        next(reader)
        
        for row in reader:
            electoral_zone_dict = {"identifier": int(row[0]), "cep": int(row[3]), "address": row[2], "neighborhood": row[4]}
            neighborhood_dict = {"name": row[4], "county_id": 0, "county_name": row[5]}
                        
            if contains_duplicates_neighborhood(neighborhood_dict, neighborhood_array):
                neighborhood_array.append(neighborhood_dict)
                
            for obj in electoral_zones_array:
                if obj["zone_id"] == electoral_zone_dict["identifier"]:
                    electoral_zone_dict["county_name"] = obj["county_name"]
                    electoral_zone_dict["state"] = obj["state"]
                                        
                    electoral_zone_complete.append(electoral_zone_dict)
                
                
    print("Terminando de selecionar bairros\n\n")
    print(neighborhood_array.__len__())
    print("\n\n")
        
    county_array_created = []
    neighborhood_array_created=[]
    electoral_zones_array_created = []
    politics_array_created = []
    political_party_array_created = []
    votes_array_created = []
    
    print("\n\nInserindo municipios\n")

    for county in county_array:
        response = requests.post(URL + "county/", data=county)
        response_json = response.json()
        county_array_created.append(response_json)
        
    print(county_array_created.__len__(), "municipios criados")

                 
    print("\n\nInserindo bairros\n")
  
    for neighborhood in neighborhood_array:
        county = next(
            (obj for obj in county_array_created if str.lower(obj["name"]) == str.lower(neighborhood["county_name"])),
            None
        )
        if county is not None:
            neighborhood["county"] = county["id"]
        else:
            print("County not found")
            break
        
        response = requests.post(URL + "neighborhood/", data=neighborhood)
        response_json = response.json()
        neighborhood_array_created.append(response_json)
    print(neighborhood_array_created.__len__(), "bairros criados")


    print("\n\nInserindo zonas eleitorais\n")

    for electoral_zone in electoral_zone_complete:
        neighborhood = next(
            (obj for obj in neighborhood_array_created 
            if str.lower(obj["name"]) == str.lower(electoral_zone["neighborhood"])),
            None
        )
        if neighborhood is not None:
            electoral_zone["neighborhood"] = neighborhood["id"]
        else:
            print("Neighborhood not found")
            break

        response = requests.post(URL + "electoral-zone/", data=electoral_zone)
        response_json = response.json()
        electoral_zones_array_created.append(response_json)
        
    print(electoral_zones_array_created.__len__(), "zonas eleitorais criadas")
    
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
        
        politics["political_type"] = 1
        politics["election"] = 1
        politics["region"] = "city"
        politics["region_id"] = county["id"]
        
        
        response = requests.post(URL + "political/", data=politics)
        response_json = response.json()
        politics_array_created.append(response_json)
    
    print(politics_array_created.__len__(), "politicos criados")
    
    print("\n\nInserindo votos\n")
    
    for votes in votes_array:
        political = next((obj for obj in politics_array_created 
                                if str.lower(obj["full_name"]) == str.lower(votes["political_full_name"]))
                               , None)
        zone = next((obj for obj in electoral_zones_array_created
                                if int(obj["identifier"]) == votes["zone_id"])
                               , None)  
        
        if political is not None:
            votes["political"] = political["id"]
        else:
            print("Political not found")
            break
        
        if zone is not None:
            votes["zone"] = zone["id"]
        else:
            print("Zone not found")
            break
        
        response = requests.post(URL + "votes/", data=votes)
        response_json = response.json()
        votes_array_created.append(response_json)
    
    print(votes_array_created.__len__(), "votos criados")

            
                    
#post_states()
base_info()
post_counties()

#python manage.py shell < cartpol_app/scripts/update_locales.py