import csv
import datetime
import functools
import shutil
from tempfile import NamedTemporaryFile

import googlemaps

gmaps = googlemaps.Client(key='AIzaSyDP-G83wGvDRkxX0-d4g5lSXHWNC2D5BxA')

filename = 'data/local_votacao_BRASIL_2016.csv'
tempfile = NamedTemporaryFile(mode='w', delete=False)

fields = ['municipio', 'municipio_id', 'UF', 'address', 'bairro', 'cep', 'seção',
          'zona', 'latitude', 'longitude', 'informacao_completa', 'local_votacao', 'distrito']


@functools.lru_cache(1024)
def find_in_maps(search_by_address, administrative_area):
    return gmaps.geocode(search_by_address, components={
        "country": "BR", "administrative_area": administrative_area}, region="BR")


startTime = datetime.datetime.now()
print("\nStarted script running at\n" + str(startTime))

i = 0
# type: ignore
with open(filename, 'r', encoding='utf-8') as csvfile, tempfile:
    reader = csv.DictReader(csvfile, fieldnames=fields,
                            delimiter=';', strict=False)
    writer = csv.DictWriter(tempfile, fieldnames=fields,
                            delimiter=';', strict=False)
    for row in reader:
        if row['bairro'] == '' or row['bairro'] is None:
            print(row)
            i += 1
            full_search_address = row['local_votacao'] + row['municipio'],
            try:
                geocode_result = find_in_maps(
                    full_search_address, row["UF"])
            except Exception as e:
                geocode_result = []
                print(f'Erro ao buscar o endereço {full_search_address}: {e}')

            if geocode_result and len(geocode_result) > 0:
                geocode_result = geocode_result[0]

                for address_component in geocode_result['address_components']:
                    if 'sublocality_level_1' in address_component["types"]:
                        row["bairro"] = address_component["long_name"]
                row['distrito'] = row['bairro']
                row['informacao_completa'] = row['latitude'] != "-1" and row['longitude'] != "-1" and row['bairro'] != ""
        row = {'municipio': row['municipio'],
               'municipio_id': row['municipio_id'],
               'UF': row['UF'],
               'address': row['address'],
               'bairro': row['bairro'],
               'cep': row['cep'],
               'UF': row['UF'],
               'seção': row['seção'],
               'zona': row['zona'],
               'latitude': row['latitude'],
               'longitude': row['longitude'],
               'informacao_completa': row['informacao_completa'],
               'local_votacao': row['local_votacao'],
               'distrito': row['distrito']}
        writer.writerow(row)

print(f"{i} bairros updated")
shutil.move(tempfile.name, filename)


print(f"\nFinished script running\nTotal time: \
      {datetime.datetime.now() - startTime}\n")
# python3 manage.py shell < cartpol_app/scripts/neighborhood_database/add_neighborhood_to_all.py
