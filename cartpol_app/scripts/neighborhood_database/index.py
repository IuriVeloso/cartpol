import googlemaps, csv, time, requests, datetime

import pandas as pd

gmaps = googlemaps.Client(key='AIzaSyAD_X42uNy1HKjuwrQXQa2YqoC6niGtdf8')

viacep = "https://viacep.com.br/ws/"

# eleitorado_local_votacao_2020
# INDEX_TURNO = 5
# INDEX_ADDRESS = 18
# INDEX_LOCAL_VOTACAO = 15
# INDEX_MUNICIPIO = 7
# INDEX_MUNICIPIO_NOME = 8
# INDEX_SG_ESTADO = 6
# INDEX_SECTION_ID = 10
# INDEX_ZONE_ID = 9
# INDEX_BAIRRO = 19
# INDEX_CEP = 20
# INDEX_LATITUDE = 22
# INDEX_LONGITUDE = 23

# votacao_secao_2020_RJ
# INDEX_ADDRESS = 25
# INDEX_LOCAL_VOTACAO = 24
# INDEX_MUNICIPIO = 14
# INDEX_SG_ESTADO = 10
# INDEX_SECTION_ID = 16
# INDEX_ZONE_ID = 15



def index(input_file, output_file):
	with open(input_file, 'r', encoding='latin-1') as f:
		reader = csv.reader(f, delimiter=';', strict=False)
		next(reader)
  
		local_votacao_obj = {}

		replicated_rows = []
		section_index = 0

		for row in reader:
			if row[INDEX_TURNO] == 2:
				continue
			section_index += 1
			address = row[INDEX_ADDRESS]
			local_votacao = row[INDEX_LOCAL_VOTACAO]
			municipio = row[INDEX_MUNICIPIO_NOME]
			municipio_id = row[INDEX_MUNICIPIO]
			section = row[INDEX_SECTION_ID]
			zone = row[INDEX_ZONE_ID]
			administrative_area = row[INDEX_SG_ESTADO]
			bairro = row[INDEX_BAIRRO]
			cep = row[INDEX_CEP]
			latitude = row[INDEX_LATITUDE]
			longitude = row[INDEX_LONGITUDE]
			full_search_address = local_votacao + ", "+ bairro + ", " + municipio

			informacao_completa = latitude != "-1" and longitude != "-1" and bairro != "-1"
   
			if (not informacao_completa) and (full_search_address in local_votacao_obj):
				latitude = local_votacao_obj[full_search_address]["latitude"]
				longitude = local_votacao_obj[full_search_address]["longitude"]
				informacao_completa = True

			if not informacao_completa:
				df = pd.read_csv("data/local_votacao_tratado_BR.csv", delimiter=';')
				result = df[df["local_votacao"] == local_votacao]
				if not result.empty:
					latitude = result["latitude"].values[0]
					longitude = result["longitude"].values[0]
					informacao_completa = True

			if not informacao_completa:
				try:
					geocode_result = gmaps.geocode(full_search_address, components={"country": "BR", "administrative_area":administrative_area}, region="BR")
				except Exception as e:
					print(f'Erro ao buscar o endereço {full_search_address}: {e}')

				if geocode_result and len(geocode_result) > 0 and geocode_result[0]['geometry']['location_type'] != 'APPROXIMATE':
					geocode_result = geocode_result[0]
					latitude = geocode_result['geometry']['location']['lat']
					longitude = geocode_result['geometry']['location']['lng']
				else:
					search_by_address = address + ", "+ bairro + ", " + municipio
					try:
						geocode_result = gmaps.geocode(search_by_address, components={"country": "BR", "administrative_area":administrative_area}, region="BR")
					except Exception as e:
						geocode_result = []
						print(f'Erro ao buscar o endereço {search_by_address}: {e}')

					if geocode_result and len(geocode_result) > 0:
						geocode_result = geocode_result[0]
						latitude = geocode_result['geometry']['location']['lat']
						longitude = geocode_result['geometry']['location']['lng']
						if geocode_result['geometry']['location_type'] != 'APPROXIMATE':
							informacao_completa = True
					else:
						print(f'Não foi possível encontrar o endereço {search_by_address}')

			local_votacao_obj[full_search_address] = {}
			local_votacao_obj[full_search_address]["latitude"] = latitude
			local_votacao_obj[full_search_address]["longitude"] = longitude
   
			if section_index % 50000 == 0:
				print(f"Section {section_index} processed")
   
			replicated_rows.append([municipio, municipio_id, administrative_area, address, bairro, cep, section, zone, latitude, longitude, informacao_completa, local_votacao])
   
	with open(output_file, 'w', encoding='utf-8', newline='') as csv_output:
		writer = csv.writer(csv_output, delimiter=';')
		writer.writerow(['municipio', 'municipio_id', 'UF', 'address', 'bairro', 'cep', 'seção', 'zona', 'latitude', 'longitude', 'informacao_completa', 'local_votacao'])
		writer.writerows(replicated_rows)

input_file = 'data/eleitorado_local_votacao_2020.csv'
output_file = 'data/local_votacao_tratado_BR_2.csv'

startTime = datetime.datetime.now()
print("\nStarted script running\n")

index(input_file, output_file)

print(f"\nFinished script running\nTotal time: {datetime.datetime.now() - startTime}\n")

#python3 manage.py shell < cartpol_app/scripts/neighborhood_database/index.py