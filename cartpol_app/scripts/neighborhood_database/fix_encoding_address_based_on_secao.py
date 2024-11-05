import pandas as pd
import re

# Configurações de tamanho do bloco
chunk_size_local = 10000  # Tamanho do bloco para local_df
chunk_size_secao = 10000  # Tamanho do bloco para secao_df

# Carrega local_df em blocos
local_df = pd.read_csv('data/local_votacao_BRASIL_2022.csv',
                       delimiter=';', encoding='utf-8')
secao_df = pd.read_csv('data/votacao_secao_2022_RJ_2.csv',
                       delimiter=';', encoding='utf-8', chunksize=chunk_size_secao)


# Cria um arquivo vazio para salvar os resultados incrementalmente
with open('data/local_corrigido_2022.csv', 'w', encoding='utf-8') as f:
    # Escreve o cabeçalho apenas uma vez
    f.write(';'.join(local_df.columns) + '\n')

# Identifica colunas para validação de caracteres incorretos (Ã ou )


# def needs_update(value):
#     # Retorna True se o valor contém "Ã" ou ""
#     return bool(re.search(r'[]', str(value)))


# columns_to_check = ['address', 'municipio', 'local_votacao']
# for col in columns_to_check:
#     local_df[col + '_needs_update'] = local_df[col].apply(needs_update)

# filtro = (local_df['UF'] == 'RJ') & ((local_df['address_needs_update']
#                                      == True) | (local_df['local_votacao_needs_update'] == True))

# # Conte o número de linhas que atendem ao filtro
# contagem = local_df[filtro]

# for index, row in contagem.iterrows():
#     print(row.to_dict())

# print(f"Número de linhas que correspondem ao filtro: {contagem.shape[0]}")

# # Função para corrigir uma linha usando blocos da secao_df


# def correct_row(row):
#     # Busca a correspondência no bloco de secao_df

#     if row['UF'] != 'RJ':
#         return row

#     if row.name % 6 == 0:
#         print(f'Processando linha {row.name}')

#     for chunck in pd.read_csv('data/votacao_secao_2022_RJ_2.csv', delimiter=';', encoding='utf-8', chunksize=chunk_size_secao):
#         match = chunck[
#             (chunck['NR_ZONA'] == row['zona']) &
#             (chunck['NR_SECAO'] == row['seção']) &
#             (chunck['CD_MUNICIPIO'] == row['municipio_id'])
#         ]

#         # Se encontrar uma correspondência, substitui os valores e encerra a busca
#         if not match.empty:
#             row.municipio = match.iloc[0]['NM_MUNICIPIO']
#             row.local_votacao = match.iloc[0]['NM_LOCAL_VOTACAO']
#             row.address = match.iloc[0]['DS_LOCAL_VOTACAO_ENDERECO']
#             break

#     return row


# # Corrige apenas as linhas que precisam de atualização
# local_df.update(local_df[local_df[[
#                 col + '_needs_update' for col in columns_to_check]].any(axis=1)].apply(correct_row, axis=1))

# # Remove as colunas de marcação de atualização
# local_df.drop(
#     columns=[col + '_needs_update' for col in columns_to_check], inplace=True)

# # Salva o DataFrame atualizado em um novo arquivo CSV
# local_df.to_csv('data/local_corrigido_2022.csv',
#                 index=False, sep=';', encoding='utf-8')


def correct_row(row, secao_chunk):
    # Busca a correspondência no bloco de secao_df
    match = secao_chunk[
        (str(secao_chunk['NR_ZONA']).strip() == str(row['zona'])) &
        (str(secao_chunk['NR_SECAO']).strip() == str(row['seção'])) &
        (str(secao_chunk['CD_MUNICIPIO']).strip() == str(row['municipio_id']))
    ]

    # Se encontrar uma correspondência, substitui os valores e encerra a busca
    if not match.empty:
        row['municipio'] = match.iloc[0]['NM_MUNICIPIO']
        row['local_votacao'] = match.iloc[0]['NM_LOCAL_VOTACAO']
        row['address'] = match.iloc[0]['DS_LOCAL_VOTACAO_ENDERECO']

    return row


# Processa o local_df em blocos
for start_local in range(0, len(local_df), chunk_size_local):
    end_local = start_local + chunk_size_local
    # Copia um bloco de local_df
    local_chunk = local_df.iloc[start_local:end_local].copy()

    # Processa cada linha do bloco de local_df
    for i, row in local_chunk.iterrows():
        # Processa secao_df em blocos até encontrar uma correspondência
        if row['UF'] != 'RJ':
            continue

        for secao_chunk in pd.read_csv('data/votacao_secao_2022_RJ_2.csv', delimiter=';', encoding='utf-8', chunksize=chunk_size_secao):
            [updated_row, found] = correct_row(row, secao_chunk)
            # Se uma correção foi feita, interrompe o loop de busca
            if found:
                local_chunk.loc[i] = updated_row
                break

    # Salva o bloco corrigido no arquivo de saída
    with open('data/local_corrigido_2022.csv', 'a', encoding='utf-8') as f:
        local_chunk.to_csv(f, header=False, index=False,
                           sep=';', encoding='utf-8')

    print(f"Bloco {start_local} - {end_local} processado e salvo.")

print("Correções aplicadas e arquivo salvo como 'local_corrigido.csv'.")

# python3 manage.py shell < cartpol_app/scripts/neighborhood_database/fix_encoding_address_based_on_secao.py
