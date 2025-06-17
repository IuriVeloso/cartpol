import pandas as pd
import numpy as np

COLS_USED_EMENDASPARLAMENTARES_POR_DOCUMENTO = [
    'Código da Emenda',
    'Código Documento',
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
    'Tipo Favorecido'
]

COLS_USED_EMENDASPARLAMENTARES_POR_FAVORECIDO = [
    'Código da Emenda',
    'Código do Favorecido',
    'UF Favorecido',
    'Município Favorecido',
    'Ano/Mês'
]

COLS_USED_CNPJ = [
    'CNPJ',
    'CEP',
    'BAIRRO'
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
    emendas_doc = pd.read_csv('data/2024_EmendasParlamentares_PorDocumento.csv', encoding='latin_1',
                              sep=';',
                              usecols=COLS_USED_EMENDASPARLAMENTARES_POR_DOCUMENTO).drop_duplicates()
    emendas_fav = pd.read_csv('data/EmendasParlamentares_PorFavorecido.csv', encoding='latin_1',
                              sep=';',
                              usecols=COLS_USED_EMENDASPARLAMENTARES_POR_FAVORECIDO).drop_duplicates()
    # cnpj_data = pd.read_csv('data/202505_CNPJ.csv', encoding='latin_1',
    #                         sep=';',
    #                         usecols=COLS_USED_CNPJ).drop_duplicates()
    # despesas = pd.read_csv('data/2024_Despesas.csv', encoding='latin_1',
    #                        sep=';',
    #                        usecols=COLS_USED_DESPESAS).drop_duplicates()

    print("Data loaded successfully.")

    # Filter emendas_doc by 'Fase da despesa' = 'Empenho'
    emendas_filtered = emendas_doc[emendas_doc['Fase da despesa'] == 'Empenho']

    print(f"Filtered emendas_doc: {len(emendas_filtered)} rows.")

    # Merge with EmendasParlamentares_PorFavorecido
    merged_df = pd.merge(
        emendas_filtered,
        emendas_fav,
        how='left',
        left_on=['Código da Emenda'],
        right_on=['Código da Emenda']
    ).drop_duplicates(inplace=True)

    print("Merging with Despesas data initializing...")

    # # Merge with Despesas
    # merged_df = pd.merge(
    #     merged_df,
    #     despesas,
    #     how='left',
    #     left_on=['Código da Emenda'],
    #     right_on=['Código Autor Emenda']
    # )

    # print("Merging with CNPJ data...")

    # # Merge with CNPJ data (preenche com NaN onde não houver correspondência)
    # final_df = pd.merge(
    #     merged_df,
    #     cnpj_data,
    #     how='left',
    #     left_on='Código do Favorecido',
    #     right_on='CNPJ'
    # )

    # print("Colunas após merge com CNPJ:\n", merged_df.columns)

    print("Final merge completed. Exporting...")
    # Export to CSV
    merged_df.to_csv('data/emendas_merged_data.csv',
                     index=False, encoding='latin-1', sep=';')

    return merged_df


if __name__ == "__main__":
    merge_emendas_data()
