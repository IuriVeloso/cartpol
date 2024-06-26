import csv, requests
from cartpol_app.scripts.database.helpers import contains_duplicates_political, contains_duplicates_political_party

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

def post_politics(url, county_array_created):
	politics_array = []
	political_party_array = []    


	with open('data/votacao_candidato_munzona_2020_BRASIL.csv', 'r', encoding='latin-1') as f:
		print("Começando a selecionar partidos e candidatos")
		
		reader = csv.reader(f, delimiter=';', strict=True)

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
				"county_name": row[INDEX_COUNTY],
				"political_id": row[INDEX_CANDIDATE_ID],
				"political_script_id": row[INDEX_POLITICAL_NUMBER],
				"county_id": row[INDEX_COUNTY_ID],
				}
				
			if int(political_dict["political_type"]) == CD_CARGO["prefeito"]:
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

	politics_index = 0

	for politics in politics_array:
		political_party = next((obj for obj in political_party_array_created 
								if obj["name"] == politics["political_party"])
								, None)
		politics_index += 1
		county = next((obj for obj in county_array_created
						if str.lower(obj["name"]).replace(" ", "") == str.lower(politics["county_name"]).replace(" ", "")), None)
		
		if political_party is not None:
			politics["political_party"] = political_party["id"]
		else:
			print("Political party not found")
			print(politics)
			break
		
		if county is not None:
			politics["region_id"] = county["id"]
		else:
			print("County not found", politics["county_name"])
			print(politics)
			break

		if politics_index % 20000 == 0:
			print(f'{round(politics_index/politics_array.__len__(), 2)}% politicos inseridos')
		
		if politics["political_type"] == CD_CARGO["prefeito"]:
			politics["political_type"] = 1
		else:
			politics["political_type"] = 2
		politics["election"] = 1
		politics["region"] = "city"
		
		
		response = requests.post(url + "political/", data=politics)
		response_json = response.json()
		response_json["political_script_id"] = politics["political_script_id"]
		response_json["county_id"] = politics["county_id"]
		politics_array_created.append(response_json)

	print(politics_array_created.__len__(), "politicos criados")
 
	return politics_array_created