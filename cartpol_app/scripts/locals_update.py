import csv, requests
from cartpol_app.scripts.helpers import contains_duplicates_electoral_zone, contains_duplicates_neighborhood, contains_duplicates_county

URL = "http://127.0.0.1:8000/cartpol/"

INDEX_SECAO = 8
INDEX_CEP = 5
INDEX_ADDRESS = 4
INDEX_ZONA = 0
INDEX_BAIRRO = 3
INDEX_MUNICIPIO = 2
INDEX_LOCAL_ID = 6

def locals_update():
  print("Começando a selecionar locais de votacao, bairros e secao")

  with open('data/local_de_votacao_RJ.csv', 'r', encoding='latin-1') as f:
    section_array = []
    neighborhood_array = []
    electoral_zones_array = []
    county_array = []        
      
    reader = csv.reader(f, delimiter=';', strict=True)
    next(reader)
      
    for row in reader:
      section_dict = {
        "identifier": row[INDEX_SECAO],
        "cep": row[INDEX_CEP],
        "address": row[INDEX_ADDRESS],
        "electoral_zone": int(row[INDEX_ZONA]),
        "electoral_zone_script_id": int(row[INDEX_ZONA]),
        "neighborhood": row[INDEX_BAIRRO],
        "script_id": row[INDEX_LOCAL_ID],
      }
      
      electoral_zones_dict = {"identifier": int(row[INDEX_ZONA]), "state": 1}
      county_dict = {"name": row[INDEX_MUNICIPIO], "state": 1}
      neighborhood_dict = {"name": row[INDEX_BAIRRO], "county_id": 2, "county_name": row[INDEX_MUNICIPIO]}

      section_array.append(section_dict)

      if contains_duplicates_neighborhood(neighborhood_dict, neighborhood_array):
        neighborhood_array.append(neighborhood_dict)

      if contains_duplicates_county(county_dict, county_array):
        county_array.append(county_dict)

      if contains_duplicates_electoral_zone(electoral_zones_dict, electoral_zones_array):
        electoral_zones_array.append(electoral_zones_dict)

  print("\nTerminando de selecionar entidades de local, começando a atualizar a base...\n")

  county_array_created = []
  neighborhood_array_created=[]
  electoral_zones_array_created = []
  section_array_created = []

  print("\nInserindo municipios\n")

  for county in county_array:
      response = requests.post(URL + "county/", data=county)
      response_json = response.json()
      county_array_created.append(response_json)
      
  print(county_array_created.__len__(), "municipios criados")


  print("\nMunicipios finalizados. Inserindo zonas eleitorais\n")

  for electoral_zone in electoral_zones_array:

      response = requests.post(URL + "electoral-zone/", data=electoral_zone)
      response_json = response.json()
      electoral_zones_array_created.append(response_json)
      
  print(electoral_zones_array_created.__len__(), "zonas eleitorais criadas")

  print("\nZ.E. finalizadas. Inserindo bairros\n")

  for neighborhood in neighborhood_array:
      county = next(
          (obj for obj in county_array_created if str.lower(obj["name"]) == str.lower(neighborhood["county_name"])),
          None
      )
      if county is not None:
          neighborhood["county"] = county["id"]
      else:
          print("County not found")
          break
      
      response = requests.post(URL + "neighborhood/", data=neighborhood)
      response_json = response.json()
      neighborhood_array_created.append(response_json)
  print(neighborhood_array_created.__len__(), "bairros criados")
  
  print("\n\nBairros finalizados. Inserindo secoes\n")

  for section in section_array:
      electoral_zone = next((obj for obj in electoral_zones_array_created 
                              if int(obj["identifier"]) == section["electoral_zone"])
                            , None)
      neighborhood = next((obj for obj in neighborhood_array_created
                              if str.lower(obj["name"]) == str.lower(section["neighborhood"]))
                              , None)
      
      if electoral_zone is None:
          print("Electoral zone not found")
          break
        
      if neighborhood is None:
          print("Neighborhood not found")
          break
      
      section["electoral_zone"] = electoral_zone["id"]
      section["neighborhood"] = neighborhood["id"]
      
      response = requests.post(URL + "section/", data=section)
      response_json = response.json()
      response_json["section_script_id"] = section["script_id"]
      response_json["electoral_zone"] = section["electoral_zone_script_id"]
      section_array_created.append(response_json)
      
  print(section_array_created.__len__(), " secoes criadas")
  return county_array_created, section_array_created

  
