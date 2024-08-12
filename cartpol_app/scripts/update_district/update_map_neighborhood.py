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
        return resp[0]["id"]
    return None


def update_map_neighborhood(url):
    with open('data/2020_map_neighbor.csv', 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';', strict=True)
        next(reader)

        for row in reader:

            county, zone_id, neighborhood, section = row[INDEX_MUNICIPIO], row[INDEX_ZONE_ID], row[INDEX_BAIRRO].strip(
            ), row[INDEX_SECTION_ID]

            section_dict = {
                "identifier": section,
                "address": str(row[INDEX_ADDRESS]).strip(),
                "electoral_zone": zone_id,
                "neighborhood": neighborhood,
                "county_name": county,
                "script_id": row[INDEX_LOCAL_ID],
            }

            section = request_section(
                f"{url}section/?identifier={section}&electoral_zone={zone_id}&county={county}")

            if section is not None:
                section_dict["section"] = section
            else:
                print("Erro na secao e foda")
                print(section_dict)
                raise Exception("Na traaaave!!!")

            r = requests.put(
                url + "section/" + section,
                json={"map_neighborhood": county},
                headers=headers)

            print(r.status_code)

    print("\nTerminando de selecionar entidades de local, começando a \
        atualizar a base...\n")
