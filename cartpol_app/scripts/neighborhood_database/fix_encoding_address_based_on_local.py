import pandas as pd
import numpy as np
import re

# Configurações de tamanho do bloco
chunk_size_local = 10000  # Tamanho do bloco para local_df
chunk_size_secao = 10000  # Tamanho do bloco para secao_df

year = 2022

# Carrega local_df em blocos
local_df = pd.read_csv(f'data/local_votacao_BRASIL_{year}.csv',
                       delimiter=';', encoding='utf-8')


# Cria um arquivo vazio para salvar os resultados incrementalmente
with open(f'data/local_corrigido_{year}.csv', 'w', encoding='utf-8') as f:
    # Escreve o cabeçalho apenas uma vez
    f.write(';'.join(local_df.columns) + '\n')

# Identifica colunas para validação de caracteres incorretos (Ã ou )


def needs_update(value):
    # Retorna True se o valor contém "Ã" ou ""
    return bool(re.search(r'[Ã]', str(value)))


columns_to_check = ['bairro', 'subdistrito']
for col in columns_to_check:
    local_df[col + '_needs_update'] = local_df[col].apply(needs_update)



# Função para corrigir uma linha usando blocos da secao_df


def correct_row(row):
    # Busca a correspondência no bloco de secao_df

    if row['UF'] != 'RJ':
        return row

    if row.name % 6 == 0:
        print(f'Processando linha {row.name}')

    for chunck in pd.read_csv(f'data/local_votacao_BRASIL_{year-2}.csv',
                              delimiter=';', encoding='utf-8', chunksize=chunk_size_secao):
        match = chunck[
            (chunck['zona'] == row['zona']) &
            (chunck['municipio_id'] == row['municipio_id']) &
            (chunck['local_votacao'] == row['local_votacao']) &
            (chunck['address'] == row['address'])
        ]

        # Se encontrar uma correspondência, substitui os valores e encerra a busca
        if not match.empty:
            row.bairro = match.iloc[0]['bairro']
            row.subdistrito = match.iloc[0]['subdistrito']
            break

    return row


# Corrige apenas as linhas que precisam de atualização
local_df.update(local_df[local_df[[
                col + '_needs_update' for col in columns_to_check]].any(axis=1)].apply(correct_row, axis=1))

# Remove as colunas de marcação de atualização
local_df.drop(
    columns=[col + '_needs_update' for col in columns_to_check], inplace=True)

# Salva o DataFrame atualizado em um novo arquivo CSV
local_df.to_csv(f'data/local_corrigido_{year}.csv',
                index=False, sep=';', encoding='utf-8')


print("Correções aplicadas e arquivo salvo como 'data/local_corrigido_.csv'.")

# python3 manage.py shell < cartpol_app/scripts/neighborhood_database/fix_encoding_address_based_on_local.py
