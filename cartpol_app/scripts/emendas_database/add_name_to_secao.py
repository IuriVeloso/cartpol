import pandas as pd
import unicodedata
import os

def normalize_name(name):
    if pd.isnull(name):
        return ''
    # Remove accents, spaces, and lowercases
    name = ''.join(
        c for c in unicodedata.normalize('NFD', str(name))
        if unicodedata.category(c) != 'Mn'
    )
    return name.replace(' ', '').lower()

# Paths
base_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(base_dir, '../../../data')
saida_path = os.path.join(data_dir, 'EmendasArquivoGeral_com_candidatos.csv')
candidatos_path = os.path.join(data_dir, 'NomeCandidato2014.csv')

# Load CSVs
saida = pd.read_csv(saida_path, dtype=str, sep=';')
candidatos = pd.read_csv(candidatos_path, dtype=str, sep=';')

# Normaliza nomes para o match
saida['nome_autor_norm'] = saida['Nome do Autor da Emenda'].apply(normalize_name)
candidatos['nome_candidato_norm'] = candidatos['NM_URNA_CANDIDATO'].apply(normalize_name)

# Colunas de candidatos a serem atualizadas (todas menos a de nome normalizado)
candidato_cols = [col for col in candidatos.columns if col != 'nome_candidato_norm']

# Faz o merge apenas para atualizar as colunas existentes
saida_atualizada = saida.merge(
    candidatos,
    left_on='nome_autor_norm',
    right_on='nome_candidato_norm',
    how='left',
    suffixes=('', '_novo')
)

# Atualiza as colunas de candidatos apenas se houver match
for col in candidato_cols:
    col_novo = f"{col}_novo"
    if col in saida_atualizada.columns and col_novo in saida_atualizada.columns:
        saida_atualizada[col] = saida_atualizada[col_novo].combine_first(saida_atualizada[col])
        saida_atualizada = saida_atualizada.drop(columns=[col_novo])

# Atualiza a coluna nome_encontrado
saida_atualizada['nome_encontrado'] = ~saida_atualizada['NM_URNA_CANDIDATO'].isnull()

# Remove colunas auxiliares
saida_atualizada = saida_atualizada.drop(columns=['nome_autor_norm', 'nome_candidato_norm'])

# Salva o resultado sobrescrevendo o arquivo de saída
saida_atualizada.to_csv(saida_path, index=False, sep=';')
print(f'Result saved to {saida_path}')
