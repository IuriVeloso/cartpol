import csv, requests, datetime, pandas as pd

startTime = datetime.datetime.now()

output_csv = 'resultado_votação_municipal_vereadores.csv'

df_votacao_secao = pd.read_csv('data/votacao_secao_RJ_2024.csv')
df_locais_votacao = pd.read_csv('data/local_votacao_BRASIL_2024.csv', delimiter=';')

lista_nomes = ['DIEGO VAZ FERREIRA','ALBERTO JACOB SZAFRAN','JOSÉ RENATO CARDOZO MOURA','TADEU AMORIM DE BARROS JUNIOR','MARCOS DIAS PEREIRA','SALVINO OLIVEIRA BARBOSA','FLAVIO GUIMARAES BITTENCOURT DO VALLE','JOYCE TRINDADE DE FARIA GAMA','TATIANA MARINS ROQUE','TAINÁ REIS DE PAULA KAPAZ','FLAVIO FERNANDO PRADO']

# Verificar e converter tipos de dados, se necessário
df_votacao_secao['NR_ZONA'] = df_votacao_secao['NR_ZONA'].astype(str)
df_votacao_secao['NR_SECAO'] = df_votacao_secao['NR_SECAO'].astype(str)
df_votacao_secao['DS_LOCAL_VOTACAO_ENDERECO'] = df_votacao_secao['DS_LOCAL_VOTACAO_ENDERECO']\
    .str.replace(r'[^a-zA-Z0-9]', '', regex=True)

df_locais_votacao['zona'] = df_locais_votacao['zona'].astype(str)
df_locais_votacao['seção'] = df_locais_votacao['seção'].astype(str)
df_locais_votacao['address'] = df_locais_votacao['address']\
    .str.replace(r'[^a-zA-Z0-9]', '', regex=True)


#---------------


def index(output_csv):
    df_merged = pd.merge(
        df_votacao_secao,
        df_locais_votacao[['zona', 'seção', 'address', 'bairro']],
        left_on=['NR_ZONA', 'NR_SECAO', 'DS_LOCAL_VOTACAO_ENDERECO'],
        right_on=['zona', 'seção', 'address'],
        how='left'
    )
    
    df_filtrado = df_merged[df_merged['NM_VOTAVEL'].isin(lista_nomes)]
    
    df_teste = df_filtrado[df_filtrado['bairro'].isna()]
    
    df_teste.to_csv('teste.csv', index=False)
    
    df_votos_bairro = df_filtrado.groupby(['NM_VOTAVEL','NR_VOTAVEL','bairro'])['QT_VOTOS'].sum().reset_index()
    
    total_votos_cidade = df_merged[df_merged['CD_MUNICIPIO'] == 60011]['QT_VOTOS'].sum()
    total_votos_por_bairro = df_merged.groupby(['CD_MUNICIPIO','bairro'])['QT_VOTOS'].sum().reset_index()
    total_votos_por_candidato = df_filtrado.groupby(['NM_VOTAVEL', 'CD_MUNICIPIO'])['QT_VOTOS'].sum().reset_index()

    total_votos_por_bairro.rename(columns={'QT_VOTOS': 'TOTAL_VOTOS_BAIRRO'}, inplace=True)
    total_votos_por_candidato.rename(columns={'QT_VOTOS': 'TOTAL_VOTOS_CANDIDATO'}, inplace=True)
    
    df_final = pd.merge(df_votos_bairro, total_votos_por_bairro, on='bairro', how='left')
    df_final = pd.merge(df_final, total_votos_por_candidato, on='NM_VOTAVEL', how='left')
    
    print(total_votos_cidade)
    
    df_final['RUESP(%)'] = df_final['TOTAL_VOTOS_BAIRRO']*100 / total_votos_cidade

    df_final['RCAN_UESP(%)'] = df_final['QT_VOTOS']*100 / df_final['TOTAL_VOTOS_BAIRRO']
    
    df_final['RUESP_CAN(%)'] = df_final['QT_VOTOS']*100 / df_final['TOTAL_VOTOS_CANDIDATO']
    
    df_final = df_final.drop(columns=['CD_MUNICIPIO_x', 'CD_MUNICIPIO_y'])
    
    df_final.rename(columns={'NM_VOTAVEL': 'nome_candidato',
                             'NR_VOTAVEL': 'numero_candidato',
                             'QT_VOTOS': 'votos_absolutos_bairro',
                             'TOTAL_VOTOS_BAIRRO': 'votos_totais_bairro',
                             'TOTAL_VOTOS_CANDIDATO': 'votos_totais_candidato'}, inplace=True)

    df_final.to_csv(output_csv, index=False)

#---------------


print("\nStarted script running at\n" + str(startTime))

index(output_csv)

print(f"\nFinished script running\nTotal time: \
      {datetime.datetime.now() - startTime}\n")

# python3 manage.py shell < cartpol_app/scripts/results/candidates_vote_neghborhood_results.py