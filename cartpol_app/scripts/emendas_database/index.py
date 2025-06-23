import pandas as pd
import numpy as np

COLS_USED_EMENDASPARLAMENTARES_POR_DOCUMENTO = [
    'Código da Emenda',
    'Ano da Emenda',
    'Tipo de Emenda',
    
    'Nome do Autor da Emenda',
    'Número da emenda',
    'Código Unidade Orçamentária',
    'Unidade Orçamentária',
    'Código Órgão SIAFI',
    'Órgão',
    'Código Órgão Superior SIAFI',
    'Órgão Superior',
    'Código Ação',
    'Ação',
    'Localidade de aplicação do recurso',
    'Código Modalidade Aplicação Despesa',
    'Modalidade Aplicação Despesa',

    'Código Função',
    'Função',
    'Código SubFunção',
    'SubFunção',

    'Código UG',
    'UG',

    'Fase da despesa',
    'Código favorecido',
    'Favorecido',
    'Tipo Favorecido',
    
    # Valores que seriam desnecessários caso consigamos fazer um merge dos dados
    'Valor Empenhado',
    'Valor Pago',
    'Código Documento'
    
]

COLS_USED_EMENDASPARLAMENTARES_POR_FAVORECIDO = [
    'Código da Emenda',
    'Código do Favorecido',
    'UF Favorecido',
    'Município Favorecido',
    'Tipo Favorecido'
]

COLS_USED_CNPJ = [
    'CNPJ',
    'CEP',
    'BAIRRO',
    'MUNICIPIO',
    'UF',
    'LOGRADOURO',
    'NUMERO',
    'COMPLEMENTO',
]

COLS_USED_NATUREZA_JURIDICA = []

COLS_USED_DESPESAS = [
    'Código Autor Emenda',
    'Valor Empenhado (R$)',
    'Valor Liquidado (R$)',
    'Valor Pago (R$)',
    'Código Gestão',
    'Nome Gestão',
]


def merge_emendas_data():
    # Load all CSV files
    emendas_doc = pd.read_csv('data/EmendasParlamentares_PorDocumento.csv', encoding='latin_1',
                              sep=';',
                              usecols=COLS_USED_EMENDASPARLAMENTARES_POR_DOCUMENTO,
                              dtype={'Código favorecido': str, 'Código Documento': str}).drop_duplicates()
    # emendas_fav = pd.read_csv('data/EmendasParlamentares_PorFavorecido.csv', encoding='latin_1',
    #                           sep=';',
    #                           usecols=COLS_USED_EMENDASPARLAMENTARES_POR_FAVORECIDO).drop_duplicates()
    cnpj_data = pd.read_csv('data/202504_CNPJ.csv', encoding='latin_1',
                            sep=';',
                            usecols=COLS_USED_CNPJ,
                            dtype={'CNPJ': str}).drop_duplicates()
    # despesas = pd.read_csv('data/2024_Despesas.csv', encoding='latin_1',
    #                        sep=';',
    #                        usecols=COLS_USED_DESPESAS).drop_duplicates()
    
    # Unifica pares de colunas código/nome em uma única coluna
    pares = [
        ('Código Unidade Orçamentária', 'Unidade Orçamentária'),
        ('Código Órgão SIAFI', 'Órgão'),
        ('Código Órgão Superior SIAFI', 'Órgão Superior'),
        ('Código Ação', 'Ação'),
        ('Código Modalidade Aplicação Despesa', 'Modalidade Aplicação Despesa'),
        ('Código Função', 'Função'),
        ('Código SubFunção', 'SubFunção'),
        ('Código UG', 'UG'),
    ]
    for cod_col, nome_col in pares:
        if cod_col in emendas_doc.columns and nome_col in emendas_doc.columns:
            emendas_doc[nome_col] = emendas_doc[cod_col].astype(str).str.strip() + ' - ' + emendas_doc[nome_col].astype(str).str.strip()
            emendas_doc = emendas_doc.drop(columns=[cod_col])

    print("Data loaded successfully.")

    # Garantir que ambos estejam como string, sem espaços e com 14 dígitos
    emendas_doc['Código favorecido'] = emendas_doc['Código favorecido'].astype(str).str.strip()
    cnpj_data['CNPJ'] = cnpj_data['CNPJ'].astype(str).str.strip()

    # Filter emendas_doc by 'Fase da despesa' = 'Empenho'
    merged_df = emendas_doc[emendas_doc['Fase da despesa'] == 'Empenho']

    print(f"Filtered emendas_doc: {len(merged_df)} rows.")

    # Adiciona coluna de link para o documento de empenho
    merged_df['Link Docs Empenho'] = merged_df['Código Documento'].apply(
        lambda x: f"https://portaldatransparencia.gov.br/despesas/documento/empenho/{x}" if pd.notnull(x) else ''
    )
    
    # Reorganiza as colunas para colocar Código favorecido, Tipo Favorecido e Favorecido no final
    cols = [col for col in merged_df.columns if col not in ['Código favorecido', 'Tipo Favorecido', 'Favorecido']]
    cols += [col for col in ['Código favorecido', 'Tipo Favorecido', 'Favorecido'] if col in merged_df.columns]
    merged_df = merged_df[cols]

    # Merge with EmendasParlamentares_PorFavorecido
    # merged_df = pd.merge(
    #     merged_df,
    #     emendas_fav,
    #     how='left',
    #     left_on=['Código da Emenda', 'Código favorecido'],
    #     right_on=['Código da Emenda', 'Código do Favorecido']
    # ).drop_duplicates()

    # print("Merging with Despesas data initializing...")

    # Merge with Despesas
    # merged_df = pd.merge(
    #     merged_df,
    #     despesas,
    #     how='left',
    #     left_on=['Código da Emenda'],
    #     right_on=['Código Autor Emenda']
    # )

    # print("Merging with CNPJ data...")

    # # Merge with CNPJ data (preenche com NaN onde não houver correspondência)
    merged_df = pd.merge(
        merged_df,
        cnpj_data,
        how='left',
        left_on='Código favorecido',
        right_on='CNPJ'
    )

    # Remove a coluna CNPJ
    if 'CNPJ' in merged_df.columns:
        merged_df = merged_df.drop(columns=['CNPJ'])

    print("Final merge completed. Exporting...")
    # Export to CSV
    merged_df.to_csv('data/EmendasArquivoGeral.csv',
                     index=False, sep=';')

    return merged_df


if __name__ == "__main__":
    merge_emendas_data()
