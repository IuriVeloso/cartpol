import csv
import functools

import requests

INDEX_SECTION_ID = 4
INDEX_ZONE_ID = 3
INDEX_LOCAL_ID = 5
# INDEX_ADDRESS = 4
INDEX_BAIRRO = 7
INDEX_MUNICIPIO = 1
INDEX_MUNICPIO_ID = 2
INDEX_FALTOU = 8

headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}


@functools.lru_cache(maxsize=8192)
def request_section(string):
    resp = requests.get(string).json()
    if len(resp) > 0:
        return resp[0]
    return None

@functools.lru_cache(maxsize=8192)
def request_county(string):
    resp = requests.get(string).json()
    if len(resp) > 0:
        return resp[0]["state"]
    return None


YEARS = [2016, 2018, 2020, 2022, 2024]


def update_map_neighborhood(url):
    for year in YEARS:
        print(f"\n\nAtualizando o ano {year}...\n")
        with open(f"data/RIOINT{year}.csv", 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=',', strict=True)
            next(reader)

            for row in reader:

                county, zone_id, neighborhood, section, county_id, faltou = row[INDEX_MUNICIPIO], row[INDEX_ZONE_ID], row[INDEX_BAIRRO].strip(
                ), str(row[INDEX_SECTION_ID]), row[INDEX_MUNICPIO_ID], row[INDEX_FALTOU]

                if faltou == '1':
                    continue
                
                county_has_id = request_county(
                    f"{url}county?name={county}&tse_id={county_id}")
                
                if county_has_id != 1:
                    continue

                section_json = request_section(
                    f"{url}section/?identifier={section}&electoral_zone={zone_id}&county_tse_id={county_id}&year={year}")

                if section_json is None and isinstance(county_id, str):
                    print("\n\nErro na secao e foda")
                    print(county, zone_id, neighborhood, section, faltou)
                    continue

                data = {
                    "map_neighborhood": neighborhood
                }

                requests.put(
                    url + "neighborhood/" + str(section_json["neighborhood"]),
                    json=data,
                    headers=headers)

        print("\nAno finalizado\n")
