import requests


def base_info(url):
    elections = [{'year': 2022, 'round': 1, 'code': 426},
                 {'year': 2020, 'round': 1, 'code': 426},
                 {'year': 2018, 'round': 1, 'code': 426},
                 {'year': 2016, 'round': 1, 'code': 426}]

    politicalTypesByElection = [
        {
            'name': "Deputado Estadual",
            'description': "Atua como representante da população no Legislativo estadual. É eleito para um mandato de quatro anos e atua nas Assembleias Legislativas, instituições presentes em todos os estados brasileiros. Tem como função legislar e fiscalizar o Executivo estadual.",
            'election': 1,
        },
        {
            'name': "Deputado Federal",
            'description': "Atua no Legislativo e tem como papel ser o representante da população na Câmara dos Deputados. O Brasil possui 513 deputados atualmente, distribuídos entre os 26 estados e o Distrito Federal. São eleitos para um mandato de quatro anos, com possibilidade de reeleição de maneira indefinida.",
            'election': 1,
        },
        {
            'name': "Senador",
            'description': "Atuam no Senado Federal, casa que faz parte do Congresso Nacional, sendo considerada a Câmara Alta. Os senadores têm funções importantes e, como parte do Legislativo, atuam como legisladores e fiscalizadores, e também podem julgar e autorizar nomeações do presidente.",
            'election': 1,
        },
        {
            'name': "Prefeito",
            'description': "Deve representar o município nas suas relações jurídicas, políticas e administrativas, além de sancionar, promulgar e publicar as leis",
            'election': 2,
        },
        {
            'name': "Vereador",
            'description': "Cabe elaborar as leis municipais e fiscalizar a atuação do Executivo – no caso, o prefeito. São os vereadores que propõem, discutem e aprovam as leis a serem aplicadas no município",
            'election': 2,
        },
        {
            'name': "Deputado Estadual",
            'description': "Atua como representante da população no Legislativo estadual.",
            'election': 3,
        },
        {
            'name': "Deputado Federal",
            'description': "Atua no Legislativo e tem como papel ser o representante da população na Câmara dos Deputados.",
            'election': 3,
        },
        {
            'name': "Senador",
            'description': "Atuam no Senado Federal, casa que faz parte do Congresso Nacional, sendo considerada a Câmara Alta.",
            'election': 3,
        },
        {
            'name': "Prefeito",
            'description': "Deve representar o município nas suas relações jurídicas, políticas e administrativas, além de sancionar, promulgar e publicar as leis",
            'election': 4,
        },
        {
            'name': "Vereador",
            'description': "Cabe elaborar as leis municipais e fiscalizar a atuação do Executivo – no caso, o prefeito. São os vereadores que propõem, discutem e aprovam as leis a serem aplicadas no município",
            'election': 4,
        }
    ]

    for election in elections:
        response_election = requests.post(url + "election/", data=election)
        response_election_json = response_election.json()
        print("\nEleicao criada:")
        print(response_election_json)

    for political_type in politicalTypesByElection:
        response = requests.post(url + "political-type/",
                                 data=political_type)
        response_json = response.json()
        print("Tipo criado:")
        print(response_json)
