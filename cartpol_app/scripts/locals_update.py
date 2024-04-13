import csv, requests, re
from cartpol_app.scripts.helpers import contains_duplicates_electoral_zone, contains_duplicates_neighborhood, contains_duplicates_county

INDEX_SECAO = "INDEX_SECAO"
INDEX_CEP="INDEX_CEP"
INDEX_ADDRESS="INDEX_ADDRESS"
INDEX_ZONA="INDEX_ZONA"
INDEX_BAIRRO="INDEX_BAIRRO"
INDEX_MUNICIPIO = "INDEX_MUNICIPIO"
INDEX_LOCAL_ID="INDEX_LOCAL_ID"

INDEX_RJ = {
  "INDEX_SECAO": 8,
  "INDEX_CEP": 5,
  "INDEX_ADDRESS": 4,
  "INDEX_ZONA": 0,
  "INDEX_BAIRRO": 3,
  "INDEX_MUNICIPIO": 2,
  "INDEX_LOCAL_ID": 6
}

INDEX_SP = {
  "INDEX_SECAO": 5,
  "INDEX_CEP": 1,
  "INDEX_ADDRESS": 4,
  "INDEX_ZONA": 1,
  "INDEX_BAIRRO": 0,
  "INDEX_MUNICIPIO": 2,
  "INDEX_LOCAL_ID": 2
}

def locals_update(url):
  print("Começando a selecionar locais de votacao, bairros e secao")
  
  INDEX_MNCP = INDEX_SP

  #with open('data/local_de_votacao_RJ.csv', 'r', encoding='latin-1') as f:
  with open('data/local_de_votacao_SP.csv', 'r', encoding='utf-8') as f:
    section_array = []
    neighborhood_array = []
    electoral_zones_array = []
    county_array = []        
      
    reader = csv.reader(f, delimiter=';', strict=True)
    next(reader)
      
    for row in reader:
      electoral_zones_dict = {"identifier": int(row[INDEX_MNCP[INDEX_ZONA]]), "state": 1}
      county_dict = {"name": "São Paulo", "state": 1}
      neighborhood_dict = {"name": str(row[INDEX_MNCP[INDEX_BAIRRO]]), "county_id": 2, "county_name": "São Paulo"}

      sections_id = row[INDEX_MNCP[INDEX_SECAO]].split(";")
      sections = []
      for item in sections_id:
          matches = re.findall(r'\b\d+(?:(?=ª)|\b)', item)
          print(matches, sections_id)
          if(len(matches) == 0):
            continue
          if (len(matches) == 1):
              sections.append(int(matches[0]))
          else:
              for i in range(int(matches[0]), int(matches[1]) + 1):
                  sections.append(i)    

      for section_id in sections:
        section_dict = {
          "identifier": section_id,
          "cep": row[INDEX_MNCP[INDEX_CEP]],
          "address": row[INDEX_MNCP[INDEX_ADDRESS]],
          "electoral_zone": int(row[INDEX_MNCP[INDEX_ZONA]]),
          "electoral_zone_script_id": int(row[INDEX_MNCP[INDEX_ZONA]]),
          "neighborhood": str(row[INDEX_MNCP[INDEX_BAIRRO]]),
          "script_id": section_id,
        }
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
      response = requests.post(url + "county/", data=county)
      response_json = response.json()
      county_array_created.append(response_json)
      
  print(county_array_created.__len__(), "municipios criados")


  print("\nMunicipios finalizados. Inserindo zonas eleitorais\n")

  for electoral_zone in electoral_zones_array:

      response = requests.post(url + "electoral-zone/", data=electoral_zone)
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
      
      response = requests.post(url + "neighborhood/", data=neighborhood)
      response_json = response.json()
      neighborhood_array_created.append(response_json)
  print(neighborhood_array_created.__len__(), "bairros criados")
  
  print("\nBairros finalizados. Inserindo secoes\n")

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
      
      response = requests.post(url + "section/", data=section)
      response_json = response.json()
      response_json["section_script_id"] = section["script_id"]
      response_json["electoral_zone"] = section["electoral_zone_script_id"]
      section_array_created.append(response_json)
      
  print(section_array_created.__len__(), " secoes criadas")
  return county_array_created, section_array_created

  
