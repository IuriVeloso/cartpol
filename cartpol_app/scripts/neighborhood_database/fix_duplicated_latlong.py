import csv
import datetime
import functools
import shutil
from tempfile import NamedTemporaryFile

import pandas as pd

filename = 'data/local_votacao_BRASIL_2018_2.csv'
tempfile = NamedTemporaryFile(mode='w', delete=False)

fields = ['municipio', 'municipio_id', 'UF', 'address', 'bairro', 'cep', 'seção',
          'zona', 'latitude', 'longitude', 'informacao_completa', 'local_votacao', 'distrito']

df_2018 = pd.read_csv(filename, delimiter=';')


@functools.lru_cache(8192)
def has_more_latlong(local_votacao, municipio_id):
    result = df_2018[(df_2018["local_votacao"] == local_votacao)
                     & (df_2018["municipio_id"] == (municipio_id))]
    result = result.drop_duplicates(subset=['latitude', 'longitude'])
    return len(result) > 1


@functools.lru_cache(8192)
def find_lat_long_replicated_value(local_votacao, municipio_id):
    result = df_2018[(df_2018["local_votacao"] == local_votacao)
                     & (df_2018["municipio_id"] == (municipio_id))]
    latitude_counts = result.value_counts(subset=['latitude', 'longitude'])

    duplicate_latitudes = latitude_counts.idxmax()
    return duplicate_latitudes[0], duplicate_latitudes[1]


startTime = datetime.datetime.now()
print("\nStarted script running at\n" + str(startTime))

i = 0
linhas = 0
# type: ignore
with open(filename, 'r', encoding='utf-8') as csvfile, tempfile:
    reader = csv.DictReader(csvfile, fieldnames=fields,
                            delimiter=';', strict=False)
    writer = csv.DictWriter(tempfile, fieldnames=fields,
                            delimiter=';', strict=False)

    next(reader)

    for row in reader:
        municipio_id = int(row["municipio_id"])
        local_votacao = row["local_votacao"]
        linhas += 1
        if has_more_latlong(local_votacao, municipio_id):
            i += 1
            if i % 100 == 0:
                print(f"Chegamos a {i}")
                print(local_votacao)
            row["latitude"], row["longitude"] = find_lat_long_replicated_value(
                local_votacao, municipio_id)

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
        if linhas % 10000 == 0:
            print(f"Finalizamos {linhas} linhas")
        writer.writerow(row)

print(f"{i} latlong fixed")
shutil.move(tempfile.name, filename)


print(f"\nFinished script running\nTotal time: \
      {datetime.datetime.now() - startTime}\n")
# python3 manage.py shell < cartpol_app/scripts/neighborhood_database/fix_duplicated_latlong.py
