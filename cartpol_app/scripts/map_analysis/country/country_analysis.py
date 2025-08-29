import geopandas as gpd
import pandas as pd

# --- DADO EXTERNO ---
# Fonte: IBGE
total_cities_by_state = {
    'Acre': 22, 'Alagoas': 102, 'Amapá': 16, 'Amazonas': 62,
    'Bahia': 417, 'Ceará': 184, 'Distrito Federal': 1, 'Espírito Santo': 78,
    'Goiás': 246, 'Maranhão': 217, 'Mato Grosso': 142, 'Mato Grosso do Sul': 79,
    'Minas Gerais': 853, 'Pará': 144, 'Paraíba': 223, 'Paraná': 399,
    'Pernambuco': 185, 'Piauí': 224, 'Rio de Janeiro': 92, 'Rio Grande do Norte': 167,
    'Rio Grande do Sul': 497, 'Rondônia': 52, 'Roraima': 15, 'Santa Catarina': 295,
    'São Paulo': 645, 'Sergipe': 75, 'Tocantins': 139
}

shapefile = 'cartpol_app\scripts\map_analysis\country\BR_bairros_CD2022\BR_bairros_CD2022.shp'
print(f"Lendo o arquivo: {shapefile}...")

try:
    districts_gdf = gpd.read_file(shapefile)
    print("Arquivo lido com sucesso!")

    # Calcular quantas cidades por estado têm bairros cadastrados
    cities_with_districts = districts_gdf.groupby('NM_UF')['NM_MUN'].nunique().reset_index()
    cities_with_districts.columns = ['Estado', 'Cidades com Bairros Cadastrados']

    # Preparar a tabela com o total de municípios
    df_total_cities = pd.DataFrame(list(total_cities_by_state.items()), columns=['Estado', 'Total de Municípios no Estado'])

    # Unir as duas tabelas
    final_tabel = pd.merge(cities_with_districts, df_total_cities, on='Estado')

    # Calcular a porcentagem de cobertura
    final_tabel['Porcentagem de Cobertura (%)'] = \
        (final_tabel['Cidades com Bairros Cadastrados'] / final_tabel['Total de Municípios no Estado']) * 100

    # Exibir o resultado final
    print("\n--- Tabela de Cobertura de Bairros por Estado ---\n")

    # Ordenar pela maior porcentagem de cobertura
    final_tabel = final_tabel.sort_values(by='Porcentagem de Cobertura (%)', ascending=False)
    
    # Formatar a coluna de porcentagem para exibir apenas 2 casas decimais
    final_tabel['Porcentagem de Cobertura (%)'] = final_tabel['Porcentagem de Cobertura (%)'].map('{:.2f}%'.format)
        
    print(final_tabel.to_string(index=False))


except FileNotFoundError:
    print(f"ERRO: O arquivo '{shapefile}' não foi encontrado. Verifique se ele está na mesma pasta do script.")
except Exception as e:
    print(f"Ocorreu um erro inesperado: {e}")