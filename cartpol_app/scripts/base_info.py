import requests

URL = "http://localhost:8000/cartpol/"

def base_info():
    election = {'year': 2020, 'round': 1, 'code': 426}
    politicalTypePrefeito = {'name': "Prefeito", 'description': "Deve representar o município nas suas relações jurídicas, políticas e administrativas, além de sancionar, promulgar e publicar as leis"}
    politicalTypeVereador = {'name': "Vereador", 'description': "Cabe elaborar as leis municipais e fiscalizar a atuação do Executivo – no caso, o prefeito. São os vereadores que propõem, discutem e aprovam as leis a serem aplicadas no município"}
    state = {'name': 'RJ', 'full_name': 'Rio de Janeiro'}
    
    response = requests.post(URL + "political-type/", data=politicalTypePrefeito)
    response_json = response.json()
    print("\nPrefeito criado:")
    print(response_json)
    
    response = requests.post(URL + "political-type/", data=politicalTypeVereador)
    response_json = response.json()
    print("\nVereador criado:")
    print(response_json)
    
    response_election = requests.post(URL + "election/", data=election)
    response_election_json = response_election.json()
    print("\nEleicao criada:")
    print(response_election_json)
    
    response_state = requests.post(URL + "state/", data=state)
    response_state_json = response_state.json()
    print("\nEstado criado:")
    print(response_state_json)
