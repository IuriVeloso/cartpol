import argparse
import datetime
import glob
import os

import pandas as pd


def load_data(year, votacao_file=None):
    """
    Carrega o arquivo CSV de votação.

    Args:
        year: Ano da eleição
        votacao_file: Caminho opcional para o arquivo de votação.
            Se None, tenta encontrar automaticamente.

    Returns:
        DataFrame de votação
    """
    # Carregar arquivo de votação
    if votacao_file is None:
        # Tentar encontrar arquivo automaticamente
        pattern = f'data/votacao_candidato_munzona*{year}*.csv'
        files = glob.glob(pattern)
        if not files:
            raise FileNotFoundError(
                f"Nenhum arquivo de votação encontrado para o ano {year}. "
                f"Padrão: {pattern}"
            )
        votacao_file = files[0]
        print(f"Usando arquivo: {votacao_file}")

    if not os.path.exists(votacao_file):
        raise FileNotFoundError(
            f"Arquivo não encontrado: {votacao_file}"
        )

    # Colunas necessárias do arquivo de votação
    votacao_cols_base = [
        'CD_MUNICIPIO', 'NM_MUNICIPIO', 'SG_UF', 'CD_CARGO',
        'SG_PARTIDO', 'NM_PARTIDO'
    ]
    # Adicionar coluna de votos (pode variar)
    votos_possiveis = [
        'QT_VOTOS_NOMINAIS', 'QT_VOTOS', 'QT_VOTOS_NOMINAIS_VALIDOS'
    ]

    # Tentar diferentes delimitadores
    try:
        # Ler apenas o cabeçalho primeiro para identificar coluna de votos
        df_test = pd.read_csv(votacao_file, delimiter=';', nrows=0)
        votacao_cols = votacao_cols_base.copy()
        for col in votos_possiveis:
            if col in df_test.columns:
                votacao_cols.append(col)
                break
        df_votacao = pd.read_csv(
            votacao_file, delimiter=';', usecols=votacao_cols
        )
    except Exception:
        # Tentar com vírgula
        df_test = pd.read_csv(votacao_file, delimiter=',', nrows=0)
        votacao_cols = votacao_cols_base.copy()
        for col in votos_possiveis:
            if col in df_test.columns:
                votacao_cols.append(col)
                break
        df_votacao = pd.read_csv(
            votacao_file, delimiter=',', usecols=votacao_cols
        )

    return df_votacao


def apply_filters(df, cargo=None, uf=None):
    """
    Aplica filtros ao dataframe de votação.

    Args:
        df: DataFrame de votação
        cargo: Código do cargo para filtrar (opcional)
        uf: Sigla do estado para filtrar (opcional)

    Returns:
        DataFrame filtrado
    """
    df_filtered = df.copy()

    if cargo is not None:
        df_filtered = df_filtered[df_filtered['CD_CARGO'] == cargo]

    if uf is not None:
        df_filtered = df_filtered[df_filtered['SG_UF'] == uf]

    return df_filtered


def calculate_indicators(df_votacao):
    """
    Calcula os indicadores RUESP, RCAN_UESP e RUESP_CAN para partidos.
    Trabalha apenas no nível estado (por município).

    Args:
        df_votacao: DataFrame com dados de votação

    Returns:
        DataFrame com indicadores calculados
    """
    # Identificar coluna de votos
    votos_col = None
    for col in ['QT_VOTOS_NOMINAIS', 'QT_VOTOS', 'QT_VOTOS_NOMINAIS_VALIDOS']:
        if col in df_votacao.columns:
            votos_col = col
            break

    if votos_col is None:
        raise ValueError(
            "Não foi possível encontrar coluna de votos. "
            f"Colunas disponíveis: {list(df_votacao.columns)}"
        )

    print("Calculando indicadores por partido e município...")

    # Agrupar por partido e município
    group_cols = [
        'SG_PARTIDO', 'NM_PARTIDO', 'CD_MUNICIPIO',
        'NM_MUNICIPIO', 'SG_UF'
    ]
    group_cols = [col for col in group_cols if col in df_votacao.columns]

    df_votos = (
        df_votacao.groupby(group_cols)[votos_col]
        .sum().reset_index()
    )
    df_votos.rename(columns={votos_col: 'QT_VOTOS'}, inplace=True)

    print(f"  - Registros após agrupamento: {len(df_votos)}")

    # Total de votos por município
    total_votos_por_municipio = (
        df_votacao.groupby(['CD_MUNICIPIO', 'SG_UF'])[votos_col]
        .sum().reset_index()
    )
    total_votos_por_municipio.rename(
        columns={votos_col: 'TOTAL_VOTOS_MUNICIPIO'}, inplace=True
    )

    # Total de votos por partido no estado
    total_votos_por_partido = (
        df_votacao.groupby(['SG_PARTIDO', 'SG_UF'])[votos_col]
        .sum().reset_index()
    )
    total_votos_por_partido.rename(
        columns={votos_col: 'TOTAL_VOTOS_PARTIDO'}, inplace=True
    )

    # Total de votos do estado
    total_votos_estado = (
        df_votacao.groupby('SG_UF')[votos_col]
        .sum().reset_index()
    )
    total_votos_estado.rename(
        columns={votos_col: 'TOTAL_VOTOS_ESTADO'}, inplace=True
    )

    # Merge dos dados
    df_final = pd.merge(
        df_votos, total_votos_por_municipio,
        on=['CD_MUNICIPIO', 'SG_UF'], how='left'
    )
    df_final = pd.merge(
        df_final, total_votos_por_partido,
        on=['SG_PARTIDO', 'SG_UF'], how='left'
    )
    df_final = pd.merge(
        df_final, total_votos_estado,
        on='SG_UF', how='left'
    )

    # Calcular indicadores
    df_final['RUESP(%)'] = (
        df_final['TOTAL_VOTOS_MUNICIPIO'] * 100
        / df_final['TOTAL_VOTOS_ESTADO']
    )
    df_final['RCAN_UESP(%)'] = (
        df_final['QT_VOTOS'] * 100
        / df_final['TOTAL_VOTOS_MUNICIPIO']
    )
    df_final['RUESP_CAN(%)'] = (
        df_final['QT_VOTOS'] * 100
        / df_final['TOTAL_VOTOS_PARTIDO']
    )

    # Calcular LQ: LQ = (E_ij / E_i) / (E_j / E)
    # Simplificando: LQ = (E_ij * E) / (E_i * E_j)
    # Onde: E_ij = QT_VOTOS, E_i = TOTAL_VOTOS_MUNICIPIO,
    #       E_j = TOTAL_VOTOS_PARTIDO, E = TOTAL_VOTOS_ESTADO
    denominator_lq = (
        df_final['TOTAL_VOTOS_MUNICIPIO'] * df_final['TOTAL_VOTOS_PARTIDO']
    )
    df_final['LQ'] = (
        df_final['QT_VOTOS'] * df_final['TOTAL_VOTOS_ESTADO']
    ) / denominator_lq
    df_final['LQ'] = df_final['LQ'].replace(
        [float('inf'), float('-inf')], pd.NA
    )

    # Calcular HC: HC = E_ij - (E_i * E_j / E)
    expected = (
        df_final['TOTAL_VOTOS_MUNICIPIO'] * df_final['TOTAL_VOTOS_PARTIDO']
    ) / df_final['TOTAL_VOTOS_ESTADO']
    df_final['HC'] = df_final['QT_VOTOS'] - expected
    df_final['HC'] = df_final['HC'].replace(
        [float('inf'), float('-inf')], pd.NA
    )

    # Calcular CI (Carvalho Index): CI = (V_i / T_V) × (P_i / T_P)
    # Onde: V_i = QT_VOTOS, T_V = TOTAL_VOTOS_PARTIDO,
    #       P_i = TOTAL_VOTOS_MUNICIPIO, T_P = TOTAL_VOTOS_ESTADO
    df_final['CI'] = (
        (df_final['QT_VOTOS'] / df_final['TOTAL_VOTOS_PARTIDO'])
        * (df_final['TOTAL_VOTOS_MUNICIPIO'] / df_final['TOTAL_VOTOS_ESTADO'])
    )
    df_final['CI'] = df_final['CI'].replace(
        [float('inf'), float('-inf')], pd.NA
    )

    # Renomear colunas
    rename_dict = {
        'SG_PARTIDO': 'sigla_partido',
        'NM_PARTIDO': 'nome_partido',
        'QT_VOTOS': 'votos_absolutos_municipio',
        'TOTAL_VOTOS_MUNICIPIO': 'votos_totais_municipio',
        'TOTAL_VOTOS_PARTIDO': 'votos_totais_partido',
        'NM_MUNICIPIO': 'municipio',
        'CD_MUNICIPIO': 'municipio_id',
        'SG_UF': 'UF'
    }
    df_final.rename(columns=rename_dict, inplace=True)

    return df_final


def main():
    """Função principal que orquestra todo o fluxo."""
    parser = argparse.ArgumentParser(
        description='Gera resultados de votação por partido '
                    'por município com indicadores (nível estado)'
    )
    parser.add_argument(
        '--year', type=int, required=True,
        help='Ano da eleição (ex: 2018, 2022)'
    )
    parser.add_argument(
        '--cargo', type=int, default=None,
        help='Código do cargo para filtrar (opcional)'
    )
    parser.add_argument(
        '--uf', type=str, default=None,
        help='Sigla do estado para filtrar (opcional)'
    )
    parser.add_argument(
        '--votacao-file', type=str, default=None,
        help='Caminho para o arquivo de votação (opcional, '
             'tenta encontrar automaticamente)'
    )
    parser.add_argument(
        '--output', type=str, default=None,
        help='Nome do arquivo de saída (opcional)'
    )

    args = parser.parse_args()

    start_time = datetime.datetime.now()
    print(f"\nIniciando execução do script em {start_time}")

    # Criar diretório de saída
    output_dir = 'cartpol_app/scripts/results/script_results'
    os.makedirs(output_dir, exist_ok=True)

    # Gerar nome do arquivo de saída se não fornecido
    if args.output is None:
        args.output = os.path.join(
            output_dir,
            f'resultado_votacao_partidos_estado_{args.year}_{args.cargo}_{args.uf}.csv'
        )
    else:
        # Se o caminho não for absoluto, salvar no diretório de saída
        if not os.path.isabs(args.output):
            args.output = os.path.join(output_dir, args.output)

    try:
        # Carregar dados
        print(f"Carregando dados para o ano {args.year}...")
        df_votacao = load_data(args.year, args.votacao_file)
        print(f"  - Votação: {len(df_votacao)} registros")

        # Aplicar filtros
        if args.cargo or args.uf:
            print("Aplicando filtros...")
            df_votacao = apply_filters(df_votacao, args.cargo, args.uf)
            print(f"  - Registros após filtros: {len(df_votacao)}")

        # Calcular indicadores
        print("Calculando indicadores para nível estado...")
        df_final = calculate_indicators(df_votacao)
        print(f"  - Registros finais: {len(df_final)}")

        # Salvar resultado
        print(f"Salvando resultado em: {args.output}")
        df_final.to_csv(args.output, index=False)

        end_time = datetime.datetime.now()
        elapsed = end_time - start_time
        print(f"\nScript finalizado em {end_time}")
        print(f"Tempo total: {elapsed}")

    except Exception as e:
        print(f"\nErro durante a execução: {e}")
        raise


if __name__ == '__main__':
    main()

# Examples:
# python cartpol_app/scripts/results/parties_vote_neghborhood_results.py \
#     --year 2018 --uf MG \
#     --cargo 6 --votacao-file data/votacao_candidato_munzona_MG_2018.csv
#
# python cartpol_app/scripts/results/parties_vote_neghborhood_results.py \
#     --year 2022 --uf RJ \
#     --cargo 6 --votacao-file data/votacao_candidato_munzona_RJ_2022.csv
