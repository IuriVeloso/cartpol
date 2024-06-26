import googlemaps, csv, time, datetime

gmaps = googlemaps.Client(key='AIzaSyAD_X42uNy1HKjuwrQXQa2YqoC6niGtdf8')

viacep = "https://viacep.com.br/ws/"

# eleitorado_local_votacao_2020
INDEX_TURNO = 5
INDEX_ADDRESS = 3
INDEX_LOCAL_VOTACAO = 11
INDEX_MUNICIPIO = 1
INDEX_MUNICIPIO_NOME = 0
INDEX_SG_ESTADO = 2
INDEX_SECTION_ID = 6
INDEX_ZONE_ID = 7
INDEX_BAIRRO = 4
INDEX_CEP = 5
INDEX_LATITUDE = 8
INDEX_LONGITUDE = 9
INDEX_FULL_INFORMATION = 10

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

		replicated_rows = []

		for row in reader:
			latitude = row[INDEX_LATITUDE]
			longitude = row[INDEX_LONGITUDE]
   
			if latitude != "-1" and longitude != "-1":
				continue
	
			address = row[INDEX_ADDRESS]
			local_votacao = row[INDEX_LOCAL_VOTACAO]
			municipio = row[INDEX_MUNICIPIO_NOME]
			municipio_id = row[INDEX_MUNICIPIO]
			section = row[INDEX_SECTION_ID]
			zone = row[INDEX_ZONE_ID]
			administrative_area = row[INDEX_SG_ESTADO]
			bairro = row[INDEX_BAIRRO]
			cep = row[INDEX_CEP]
			informacao_completa = row[INDEX_FULL_INFORMATION]

			search_by_address = address + ", "+ bairro + ", " + municipio

			try:
				geocode_result = gmaps.geocode(search_by_address, components={"country": "BR", "administrative_area":administrative_area}, region="BR")
				time.sleep(0.1)
			except Exception as e:
				geocode_result = []
				print(f'Erro ao buscar o endereço {search_by_address}: {e}')

			if geocode_result and len(geocode_result) > 0:
				print(geocode_result)
				geocode_result = geocode_result[0]
				latitude = geocode_result['geometry']['location']['lat']
				longitude = geocode_result['geometry']['location']['lng']
				if geocode_result['geometry']['location_type'] != 'APPROXIMATE':
					informacao_completa = True
			else:
				print(f'Não foi possível encontrar o endereço {search_by_address}')
   
			replicated_rows.append([municipio, municipio_id, administrative_area, address, bairro, cep, section, zone, latitude, longitude, informacao_completa, local_votacao])
   
	with open(output_file, 'w', encoding='utf-8', newline='') as csv_output:
		writer = csv.writer(csv_output, delimiter=';')
		writer.writerow(['municipio', 'municipio_id', 'UF', 'address', 'bairro', 'cep', 'seção', 'zona', 'latitude', 'longitude', 'informacao_completa', 'local_votacao'])
		writer.writerows(replicated_rows)

input_file = 'data/votacao_secao_2020_RJ.csv'
output_file = 'data/local_votacao_tratado_BR_3.csv'

startTime = datetime.datetime.now()
print("\nStarted script running\n")

index(input_file, output_file)

print(f"\nFinished script running\nTotal time: {datetime.datetime.now() - startTime}\n")

#python3 manage.py shell < cartpol_app/scripts/neighborhood_database/index.py