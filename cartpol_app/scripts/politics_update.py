import csv, requests
from cartpol_app.scripts.helpers import contains_duplicates_political, contains_duplicates_political_party

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
INDEX_POLITICAL_NUMBER = 19

def post_politics(url, county_array_created):
	politics_array = []
	political_party_array = []    


	with open('data/votacao_candidato_munzona_2020_RJ.csv', 'r', encoding='latin-1') as f:
		print("Começando a selecionar partidos e candidatos")
		
		reader = csv.reader(f, delimiter=';', strict=True)

		next(reader)

		for row in reader:
			political_dict = {
				"election": 1, 
				"name": row[INDEX_NAME], 
				"full_name": row[INDEX_FULL_NAME], 
				"political_party": row[INDEX_POLITICAL_PARTY], 
				"political_type": row[INDEX_CARGO],
				"county_name": row[INDEX_COUNTY],
				"political_id": row[INDEX_CANDIDATE_ID],
				"political_script_id": row[INDEX_POLITICAL_NUMBER],
				"county_id": row[INDEX_COUNTY_ID],
				}
   
			# Removendo votos nulos e restringindo a 5 municipios principais do RJ
			if row[INDEX_CANDIDATE_ID] in ['95', '96']:
				continue
			
				
			if int(political_dict["political_type"]) == CD_CARGO["prefeito"] and row[INDEX_ELECTION_CODE] == "426" and row[INDEX_ROUND] == "1":
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
				if political_dict["political_id"].__len__() < 4 :
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
		
		response = requests.post(url + "political-party/", data=political_party)
		response_json = response.json()
		political_party_array_created.append(response_json)
		
	print(political_party_array_created.__len__(), "partidos criados")
	print("\n\nPartidos finalizados. Inserindo politicos\n")

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
		
		
		response = requests.post(url + "political/", data=politics)
		response_json = response.json()
		response_json["political_script_id"] = politics["political_script_id"]
		response_json["county_id"] = politics["county_id"]
		politics_array_created.append(response_json)

	print(politics_array_created.__len__(), "politicos criados")
 
	return politics_array_created