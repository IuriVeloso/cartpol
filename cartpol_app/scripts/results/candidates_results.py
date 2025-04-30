import requests
import csv

# Configurações
base_url = "http://127.0.0.1:8000/cartpol/political-votes/{deputado}?county_id={municipio}"
output_csv = "political_votes_results.csv"

# Deputados estaduais e federais
deputados = {
    "Vereador": {
        "633612": "ALBERTO SZAFRAN",
        "633406": "DIEGO VAZ",
        "645169": "FLAVIO GANEM",
        "641956": "FLÁVIO VALLE",
        "642328": "JOYCE TRINDADE",
        "634426": "JUNIOR DA LUCINHA",
        "634632": "MARCOS DIAS",
        "633983": "RENATO MOURA",
        "641809": "SALVINO OLIVEIRA",
        "644989": "TAINÁ DE PAULA",
        "644853": "TATIANA ROQUE"
    }
}

# Municípios
municipios = {
    "2": "Rio de Janeiro",
}

# Função principal
def fetch_and_save_votes():
    with open(output_csv, mode="w", newline="", encoding="utf-8") as csvfile:
        csv_writer = csv.writer(csvfile)
        # Cabeçalho do CSV
        csv_writer.writerow(["Deputado", "Tipo", "Municipio", "Votos No Municipio", "Bairro", "Votos No Bairro", "RCAN_UESP", "RUESP_CAN", "RUESP"])
        
        for tipo, deputado_dict in deputados.items():
            for deputado_id, deputado_nome in deputado_dict.items():
                for municipio_id, municipio_nome in municipios.items():
                    # Construir a URL
                    url = base_url.format(deputado=deputado_id, municipio=municipio_id)
                    try:
                        # Fazer a requisição
                        response = requests.get(url).json()
                        for data in response['votes_by_neighborhood']:
                            csv_writer.writerow([deputado_nome, tipo, municipio_nome, response['total_political_votes'] ,data['neighborhood'], data['total_votes'], data['rcan_uesp'],  data['ruesp_can'],  data['ruesp']])

                    except requests.RequestException as e:
                        # Capturar erros
                        resposta = f"Erro: {str(e)}"
                    
                    # Escrever no CSV
                    
                    print(f"Processado: {deputado_nome} ({tipo}) - {municipio_nome}")

fetch_and_save_votes()
    
# python3 manage.py shell < cartpol_app/scripts/results/candidates_results.py