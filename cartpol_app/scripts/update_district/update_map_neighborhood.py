import csv
import functools

import requests

INDEX_SECTION_ID = 3
INDEX_ZONE_ID = 2
INDEX_LOCAL_ID = 4
# INDEX_ADDRESS = 4
INDEX_BAIRRO = 6
INDEX_MUNICIPIO = 0
INDEX_MUNICPIO_ID = 1

headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}


@functools.lru_cache(maxsize=8192)
def request_section(string):
    resp = requests.get(string).json()
    if len(resp) > 0:
        return resp[0]
    return None


YEAR = 2022


def update_map_neighborhood(url):
    with open(f"data/RJESTD{YEAR}.xlsx - Sheet1.csv", 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=',', strict=True)
        next(reader)

        for row in reader:

            county, zone_id, neighborhood, section, county_id = row[INDEX_MUNICIPIO], row[INDEX_ZONE_ID], row[INDEX_BAIRRO].strip(
            ), str(row[INDEX_SECTION_ID]), row[INDEX_MUNICPIO_ID]

            if county == 'DUQUE DE CAXIAS' or county == '':
                continue

            section_json = request_section(
                f"{url}section/?identifier={section}&electoral_zone={zone_id}&county_tse_id={county_id}&year={YEAR}")

            if section_json is None and isinstance(county_id, str):
                print("Erro na secao e foda")
                print(county, zone_id, neighborhood, section)
                raise Exception("Na traaaave!!!")

            data = {
                "map_neighborhood": neighborhood
            }

            requests.put(
                url + "neighborhood/" + str(section_json["neighborhood"]),
                json=data,
                headers=headers)

    print("\nTerminando de selecionar entidades de local, começando a \
        atualizar a base...\n")
