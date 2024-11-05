import csv
import datetime
import functools

import googlemaps
import pandas as pd
import os

GMAPS_KEY = os.getenv("GMAPS_KEY", default="abc")

gmaps = googlemaps.Client(key=GMAPS_KEY)

viacep = "https://viacep.com.br/ws/"

# eleitorado_local_votacao_2020
# INDEX_TURNO = 5
# INDEX_ADDRESS = 3
# INDEX_LOCAL_VOTACAO = 11
# INDEX_MUNICIPIO = 1
# INDEX_MUNICIPIO_NOME = 0
# INDEX_SG_ESTADO = 2
# INDEX_SECTION_ID = 6
# INDEX_ZONE_ID = 7
# INDEX_BAIRRO = 4
# INDEX_CEP = 5
# INDEX_LATITUDE = 8
# INDEX_LONGITUDE = 9
# INDEX_FULL_INFORMATION = 10

# votacao_secao_2020_SP
INDEX_ADDRESS = 25
INDEX_LOCAL_VOTACAO = 24
INDEX_MUNICIPIO = 13
INDEX_MUNICIPIO_NOME = 14
INDEX_SG_ESTADO = 10
INDEX_SECTION_ID = 16
INDEX_ZONE_ID = 15
INDEX_TURNO = 5


@functools.lru_cache(8192)
def find_in_maps(search_by_address, administrative_area):
    return gmaps.geocode(search_by_address, components={
        "country": "BR", "administrative_area": administrative_area}, region="BR")


df = pd.read_csv('data/local_votacao_BRASIL_2018.csv', delimiter=';')

df_2020 = pd.read_csv('data/local_votacao_BRASIL_2020.csv', delimiter=';')
df_2022 = pd.read_csv('data/local_votacao_BRASIL_2024.csv', delimiter=';')
df_2018 = pd.read_csv('data/local_votacao_BRASIL_2016.csv', delimiter=';')
# df_2016 = pd.read_csv('data/local_votacao_BRASIL_2022.csv', delimiter=';')


@functools.lru_cache(4096)
def find_in_local_votacao(local_votacao, municipio_id):
    result = df_2022[(df_2022["local_votacao"] == local_votacao)
                     & (df_2022["municipio_id"] == municipio_id)]
    if not result.empty:
        return result

    result = df_2020[(df_2020["local_votacao"] == local_votacao)
                     & (df_2020["municipio_id"] == municipio_id)]

    if not result.empty:
        return result

    result = df_2018[(df_2018["local_votacao"] == local_votacao)
                     & (df_2018["municipio_id"] == municipio_id)]

    # if not result.empty:
    #     return result

    # result = df_2016[(df_2016["local_votacao"] == local_votacao)
    #                  & (df_2016["municipio_id"] == municipio_id)]

    return result


@functools.lru_cache(4096)
def find_in_same_year_local_votacao(local_votacao, municipio_id):
    result = df[(df["local_votacao"] == local_votacao)
                & (df["municipio_id"] == municipio_id)]
    return (not result.empty)


def index(input_section_file, output_file):
    with open(input_section_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';', strict=False)
        next(reader)

        replicated_rows = []
        found_keys = {}
        section_index = 0
        for row in reader:
            section_index += 1
            local_votacao = row[INDEX_LOCAL_VOTACAO]
            municipio_id = row[INDEX_MUNICIPIO]
            address = row[INDEX_ADDRESS]
            section = row[INDEX_SECTION_ID]
            zone = row[INDEX_ZONE_ID]
            key = (zone+section+address)

            if (find_in_same_year_local_votacao(local_votacao, int(municipio_id))) or (key in found_keys):
                continue

            municipio = row[INDEX_MUNICIPIO_NOME]
            administrative_area = row[INDEX_SG_ESTADO]
            informacao_completa = False
            bairro = ''
            cep = ''
            subdistrito = ''

            search_by_address = local_votacao + ", " + municipio

            if not informacao_completa:
                result = find_in_local_votacao(
                    local_votacao, int(municipio_id))
                if not result.empty:
                    latitude = result["latitude"].values[0]
                    longitude = result["longitude"].values[0]
                    bairro = result["bairro"].values[0]
                    cep = result["cep"].values[0]
                    subdistrito = result["subdistrito"].values[0]
                    informacao_completa = True

            if not informacao_completa:
                try:
                    geocode_result = find_in_maps(
                        search_by_address, administrative_area)
                except Exception as e:
                    geocode_result = []
                    print(f'Erro ao buscar o endereço {
                          search_by_address}: {e}')

                if geocode_result and len(geocode_result) > 0:
                    geocode_result = geocode_result[0]

                    for address_component in geocode_result['address_components']:
                        if 'postal_code' in address_component["types"]:
                            cep = address_component["long_name"]
                        if 'sublocality_level_1' in address_component["types"]:
                            bairro = address_component["long_name"]
                            subdistrito = bairro

                    latitude = geocode_result['geometry']['location']['lat']
                    longitude = geocode_result['geometry']['location']['lng']
                    if geocode_result['geometry']['location_type'] != 'APPROXIMATE':
                        informacao_completa = True
                else:
                    print("Não foi possível encontrar o endereço "
                          + search_by_address)

            if section_index % 50000 == 0:
                print(f"{section_index} sections finished")
            found_keys[key] = True
            replicated_rows.append([municipio, municipio_id, administrative_area, address, bairro, cep,
                                   section, zone, latitude, longitude, informacao_completa, local_votacao, subdistrito])

        find_in_maps.cache_clear()
        find_in_same_year_local_votacao.cache_clear()
        find_in_local_votacao.cache_clear()

    with open(output_file, 'a', encoding='utf-8', newline='') as csv_output:
        writer = csv.writer(csv_output, delimiter=';')
        for row in replicated_rows:
            writer.writerow(row)


input_section_file = 'data/votacao_secao_2018_RJ_2.csv'
output_file = 'data/local_votacao_BRASIL_2018.csv'

startTime = datetime.datetime.now()
print("\nStarted script running at\n" + str(startTime))

index(input_section_file, output_file)

print(f"\nFinished script running\nTotal time: \
      {datetime.datetime.now() - startTime}\n")

# python3 manage.py shell < cartpol_app/scripts/neighborhood_database/add_votacao_secao_to_local_votacao.py
