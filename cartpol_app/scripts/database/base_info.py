import requests

def base_info(url):
    election = {'year': 2020, 'round': 1, 'code': 426}
    politicalTypePrefeito = {'name': "Prefeito", 'description': "Deve representar o município nas suas relações jurídicas, políticas e administrativas, além de sancionar, promulgar e publicar as leis"}
    politicalTypeVereador = {'name': "Vereador", 'description': "Cabe elaborar as leis municipais e fiscalizar a atuação do Executivo – no caso, o prefeito. São os vereadores que propõem, discutem e aprovam as leis a serem aplicadas no município"}
    
    response = requests.post(url + "political-type/", data=politicalTypePrefeito)
    response_json = response.json()
    print("\nPrefeito criado:")
    print(response_json)
    
    response = requests.post(url + "political-type/", data=politicalTypeVereador)
    response_json = response.json()
    print("\nVereador criado:")
    print(response_json)
    
    response_election = requests.post(url + "election/", data=election)
    response_election_json = response_election.json()
    print("\nEleicao criada:")
    print(response_election_json)
