import csv
import functools

import requests

INDEX_SECTION_ID = 2
INDEX_ZONE_ID = 1
INDEX_LOCAL_ID = 3
INDEX_ADDRESS = 4
INDEX_BAIRRO = 5
INDEX_MUNICIPIO = 0

headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}


@functools.lru_cache(maxsize=8192)
def request_section(string):
    resp = requests.get(string).json()
    if len(resp) > 0:
        return resp[0]
    return None


def update_map_neighborhood(url):
    with open('data/2020_map_neighbor.csv', 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=',', strict=True)
        next(reader)

        for row in reader:

            county, zone_id, neighborhood, section = row[INDEX_MUNICIPIO], row[INDEX_ZONE_ID], row[INDEX_BAIRRO].strip(
            ), str(row[INDEX_SECTION_ID])

            section_json = request_section(
                f"{url}section/?identifier={section}&electoral_zone={zone_id}&county={county}")

            if section_json is None:
                print("Erro na secao e foda")
                print(county, zone_id, neighborhood, section)
                raise Exception("Na traaaave!!!")

            data = {
                "electoral_zone": section_json["electoral_zone"],
                "neighborhood": section_json["neighborhood"],
                "identifier": section_json["identifier"],
                "map_neighborhood": neighborhood
            }

            requests.put(
                url + "section/" + str(section_json["id"]),
                json=data,
                headers=headers)

    print("\nTerminando de selecionar entidades de local, começando a \
        atualizar a base...\n")
