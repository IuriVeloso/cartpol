import argparse
import datetime
import glob
import os

import pandas as pd


def load_data(year, votacao_file=None):
    """
    Carrega os arquivos CSV de votação e locais de votação.

    Args:
        year: Ano da eleição
        votacao_file: Caminho opcional para o arquivo de votação.
            Se None, tenta encontrar automaticamente.

    Returns:
        tuple: (df_votacao_secao, df_locais_votacao)
    """
    # Carregar arquivo de locais de votação
    locais_file = f'data/local_votacao_BRASIL_{year}.csv'
    if not os.path.exists(locais_file):
        raise FileNotFoundError(
            f"Arquivo não encontrado: {locais_file}"
        )

    df_locais_votacao = pd.read_csv(locais_file, delimiter=';')

    # Carregar arquivo de votação
    if votacao_file is None:
        # Tentar encontrar arquivo automaticamente
        pattern = f'data/votacao_secao*{year}*.csv'
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

    df_votacao_secao = pd.read_csv(votacao_file, delimiter=';')

    return df_votacao_secao, df_locais_votacao


def apply_filters(df, municipio_id=None, cargo=None, uf=None):
    """
    Aplica filtros ao dataframe de votação.

    Args:
        df: DataFrame de votação
        municipio_id: ID do município para filtrar (opcional)
        cargo: Código do cargo para filtrar (opcional)
        uf: Sigla do estado para filtrar (opcional)

    Returns:
        DataFrame filtrado
    """
    df_filtered = df.copy()

    if municipio_id is not None:
        print(f"Filtrando por município: {municipio_id}")
        df_filtered = df_filtered[
            df_filtered['CD_MUNICIPIO'] == municipio_id
        ]

    if cargo is not None:
        df_filtered = df_filtered[df_filtered['CD_CARGO'] == cargo]

    if uf is not None:
        df_filtered = df_filtered[df_filtered['SG_UF'] == uf]

    return df_filtered


def normalize_data(df_votacao, df_locais):
    """
    Normaliza os tipos de dados e formata colunas para merge.

    Args:
        df_votacao: DataFrame de votação
        df_locais: DataFrame de locais de votação

    Returns:
        tuple: (df_votacao_normalized, df_locais_normalized)
    """
    df_votacao = df_votacao.copy()
    df_locais = df_locais.copy()

    # Normalizar votação
    df_votacao['NR_ZONA'] = df_votacao['NR_ZONA'].astype(str)
    df_votacao['NR_SECAO'] = df_votacao['NR_SECAO'].astype(str)
    if 'DS_LOCAL_VOTACAO_ENDERECO' in df_votacao.columns:
        df_votacao['DS_LOCAL_VOTACAO_ENDERECO'] = (
            df_votacao['DS_LOCAL_VOTACAO_ENDERECO']
            .str.replace(r'[^a-zA-Z0-9]', '', regex=True)
        )

    # Normalizar locais
    df_locais['zona'] = df_locais['zona'].astype(str)
    df_locais['seção'] = df_locais['seção'].astype(str)
    if 'address' in df_locais.columns:
        df_locais['address'] = (
            df_locais['address']
            .str.replace(r'[^a-zA-Z0-9]', '', regex=True)
        )

    return df_votacao, df_locais


def process_data(df_votacao, df_locais):
    """
    Processa e faz merge dos dataframes de votação e locais.

    Args:
        df_votacao: DataFrame de votação
        df_locais: DataFrame de locais de votação

    Returns:
        DataFrame merged
    """
    # Normalizar dados
    df_votacao, df_locais = normalize_data(df_votacao, df_locais)

    # Selecionar colunas necessárias do df_locais
    locais_cols = [
        'zona', 'seção', 'address', 'bairro',
        'municipio', 'municipio_id', 'UF'
    ]
    locais_cols = [col for col in locais_cols if col in df_locais.columns]

    # Fazer merge
    # Se for cargo 1 (presidente), fazer merge apenas por zona e seção; senão inclui endereço
    loc_left_on = ['NR_ZONA', 'NR_SECAO']
    loc_right_on = ['zona', 'seção']
    if 'CD_CARGO' in df_votacao.columns and (df_votacao['CD_CARGO'] == 1).all():
        # Presidente: só por zona e seção
        pass
    else:
        # Outros cargos: incluir endereço
        loc_left_on.append('DS_LOCAL_VOTACAO_ENDERECO')
        loc_right_on.append('address')
    df_merged = pd.merge(
        df_votacao,
        df_locais[locais_cols],
        left_on=loc_left_on,
        right_on=loc_right_on,
        how='left'
    )

    return df_merged


def calculate_indicators(df_merged, level='municipio'):
    """
    Calcula os indicadores RUESP, RCAN_UESP e RUESP_CAN.

    Args:
        df_merged: DataFrame merged com dados de votação e locais
        level: Nível de análise ('municipio' ou 'estado')

    Returns:
        DataFrame com indicadores calculados
    """
    if level == 'municipio':
        # Agrupar por candidato e bairro
        group_cols = [
            'NM_VOTAVEL', 'NR_VOTAVEL', 'SG_PARTIDO', 'bairro',
            'CD_MUNICIPIO', 'NM_MUNICIPIO', 'SG_UF'
        ]
        group_cols = [
            col for col in group_cols if col in df_merged.columns
        ]

        df_votos = (
            df_merged.groupby(group_cols)['QT_VOTOS']
            .sum().reset_index()
        )

        # Total de votos por bairro (dentro do município)
        total_votos_por_bairro = (
            df_merged.groupby(['CD_MUNICIPIO', 'bairro'])['QT_VOTOS']
            .sum().reset_index()
        )
        total_votos_por_bairro.rename(
            columns={'QT_VOTOS': 'TOTAL_VOTOS_BAIRRO'}, inplace=True
        )

        # Total de votos por candidato no município
        total_votos_por_candidato = (
            df_merged.groupby(['NM_VOTAVEL', 'CD_MUNICIPIO'])['QT_VOTOS']
            .sum().reset_index()
        )
        total_votos_por_candidato.rename(
            columns={'QT_VOTOS': 'TOTAL_VOTOS_CANDIDATO'}, inplace=True
        )

        # Total de votos do município
        total_votos_municipio = (
            df_merged.groupby('CD_MUNICIPIO')['QT_VOTOS']
            .sum().reset_index()
        )
        total_votos_municipio.rename(
            columns={'QT_VOTOS': 'TOTAL_VOTOS_MUNICIPIO'}, inplace=True
        )

        # Merge dos dados
        df_final = pd.merge(
            df_votos, total_votos_por_bairro,
            on=['CD_MUNICIPIO', 'bairro'], how='left'
        )
        df_final = pd.merge(
            df_final, total_votos_por_candidato,
            on=['NM_VOTAVEL', 'CD_MUNICIPIO'], how='left'
        )
        df_final = pd.merge(
            df_final, total_votos_municipio,
            on='CD_MUNICIPIO', how='left'
        )

        # Calcular indicadores
        df_final['RUESP(%)'] = (
            df_final['TOTAL_VOTOS_BAIRRO'] * 100
            / df_final['TOTAL_VOTOS_MUNICIPIO']
        )
        df_final['RCAN_UESP(%)'] = (
            df_final['QT_VOTOS'] * 100
            / df_final['TOTAL_VOTOS_BAIRRO']
        )
        df_final['RUESP_CAN(%)'] = (
            df_final['QT_VOTOS'] * 100
            / df_final['TOTAL_VOTOS_CANDIDATO']
        )

        # Calcular LQ: LQ = (E_ij / E_i) / (E_j / E)
        # Simplificando: LQ = (E_ij * E) / (E_i * E_j)
        # Onde: E_ij = QT_VOTOS, E_i = TOTAL_VOTOS_BAIRRO,
        #       E_j = TOTAL_VOTOS_CANDIDATO, E = TOTAL_VOTOS_MUNICIPIO
        total_bairro = df_final['TOTAL_VOTOS_BAIRRO']
        total_candidato = df_final['TOTAL_VOTOS_CANDIDATO']
        denominator_lq = total_bairro * total_candidato
        df_final['LQ'] = (
            df_final['QT_VOTOS'] * df_final['TOTAL_VOTOS_MUNICIPIO']
        ) / denominator_lq
        df_final['LQ'] = df_final['LQ'].replace(
            [float('inf'), float('-inf')], pd.NA
        )

        # Calcular HC: HC = E_ij - (E_i * E_j / E)
        expected = (
            total_bairro * total_candidato
        ) / df_final['TOTAL_VOTOS_MUNICIPIO']
        df_final['HC'] = df_final['QT_VOTOS'] - expected
        df_final['HC'] = df_final['HC'].replace(
            [float('inf'), float('-inf')], pd.NA
        )

        # Renomear colunas
        rename_dict = {
            'NM_VOTAVEL': 'nome_candidato',
            'NR_VOTAVEL': 'numero_candidato',
            'QT_VOTOS': 'votos_absolutos_bairro',
            'TOTAL_VOTOS_BAIRRO': 'votos_totais_bairro',
            'TOTAL_VOTOS_CANDIDATO': 'votos_totais_candidato',
            'NM_MUNICIPIO': 'municipio',
            'CD_MUNICIPIO': 'municipio_id',
            'SG_UF': 'UF'
        }
        # Adicionar SG_PARTIDO se existir
        if 'SG_PARTIDO' in df_final.columns:
            rename_dict['SG_PARTIDO'] = 'SG_PARTIDO'
        df_final.rename(columns=rename_dict, inplace=True)

    elif level == 'estado':
        # Agrupar por candidato e município
        group_cols = [
            'NM_VOTAVEL', 'NR_VOTAVEL', 'SG_PARTIDO', 'CD_MUNICIPIO',
            'NM_MUNICIPIO', 'SG_UF'
        ]
        group_cols = [
            col for col in group_cols if col in df_merged.columns
        ]

        df_votos = (
            df_merged.groupby(group_cols)['QT_VOTOS']
            .sum().reset_index()
        )

        # Total de votos por município
        total_votos_por_municipio = (
            df_merged.groupby(['CD_MUNICIPIO', 'SG_UF'])['QT_VOTOS']
            .sum().reset_index()
        )
        total_votos_por_municipio.rename(
            columns={'QT_VOTOS': 'TOTAL_VOTOS_MUNICIPIO'}, inplace=True
        )

        # Total de votos por candidato no estado
        total_votos_por_candidato = (
            df_merged.groupby(['NM_VOTAVEL', 'SG_UF'])['QT_VOTOS']
            .sum().reset_index()
        )
        total_votos_por_candidato.rename(
            columns={'QT_VOTOS': 'TOTAL_VOTOS_CANDIDATO'}, inplace=True
        )

        # Total de votos do estado
        total_votos_estado = (
            df_merged.groupby('SG_UF')['QT_VOTOS']
            .sum().reset_index()
        )
        total_votos_estado.rename(
            columns={'QT_VOTOS': 'TOTAL_VOTOS_ESTADO'}, inplace=True
        )

        # Merge dos dados
        df_final = pd.merge(
            df_votos, total_votos_por_municipio,
            on=['CD_MUNICIPIO', 'SG_UF'], how='left'
        )
        df_final = pd.merge(
            df_final, total_votos_por_candidato,
            on=['NM_VOTAVEL', 'SG_UF'], how='left'
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
            / df_final['TOTAL_VOTOS_CANDIDATO']
        )

        # Calcular LQ: LQ = (E_ij / E_i) / (E_j / E)
        # Simplificando: LQ = (E_ij * E) / (E_i * E_j)
        # Onde: E_ij = QT_VOTOS, E_i = TOTAL_VOTOS_MUNICIPIO,
        #       E_j = TOTAL_VOTOS_CANDIDATO, E = TOTAL_VOTOS_ESTADO
        total_municipio = df_final['TOTAL_VOTOS_MUNICIPIO']
        total_candidato = df_final['TOTAL_VOTOS_CANDIDATO']
        denominator_lq = total_municipio * total_candidato
        df_final['LQ'] = (
            df_final['QT_VOTOS'] * df_final['TOTAL_VOTOS_ESTADO']
        ) / denominator_lq
        df_final['LQ'] = df_final['LQ'].replace(
            [float('inf'), float('-inf')], pd.NA
        )

        # Calcular HC: HC = E_ij - (E_i * E_j / E)
        expected = (
            total_municipio * total_candidato
        ) / df_final['TOTAL_VOTOS_ESTADO']
        df_final['HC'] = df_final['QT_VOTOS'] - expected
        df_final['HC'] = df_final['HC'].replace(
            [float('inf'), float('-inf')], pd.NA
        )

        # Renomear colunas
        rename_dict = {
            'NM_VOTAVEL': 'nome_candidato',
            'NR_VOTAVEL': 'numero_candidato',
            'QT_VOTOS': 'votos_absolutos_municipio',
            'TOTAL_VOTOS_MUNICIPIO': 'votos_totais_municipio',
            'TOTAL_VOTOS_CANDIDATO': 'votos_totais_candidato',
            'NM_MUNICIPIO': 'municipio',
            'CD_MUNICIPIO': 'municipio_id',
            'SG_UF': 'UF'
        }
        # Adicionar SG_PARTIDO se existir
        if 'SG_PARTIDO' in df_final.columns:
            rename_dict['SG_PARTIDO'] = 'SG_PARTIDO'
        df_final.rename(columns=rename_dict, inplace=True)
    else:
        raise ValueError(
            f"Nível de análise inválido: {level}. "
            "Use 'municipio' ou 'estado'."
        )

    return df_final


def main():
    """Função principal que orquestra todo o fluxo."""
    parser = argparse.ArgumentParser(
        description='Gera resultados de votação por bairro/município '
                    'com indicadores'
    )
    parser.add_argument(
        '--year', type=int, required=True,
        help='Ano da eleição (ex: 2018, 2022)'
    )
    parser.add_argument(
        '--level', type=str, choices=['municipio', 'estado'], required=True,
        help='Nível de análise: municipio ou estado'
    )
    parser.add_argument(
        '--municipio-id', type=int, default=None,
        help='ID do município para filtrar (opcional)'
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
        level_suffix = (
            'municipio' if args.level == 'municipio' else 'estado'
        )
        args.output = os.path.join(
            output_dir,
            f'resultado_votacao_{level_suffix}_{args.year}_{args.cargo}_{args.uf}.csv'
        )
    else:
        # Se o caminho não for absoluto, salvar no diretório de saída
        if not os.path.isabs(args.output):
            args.output = os.path.join(output_dir, args.output)

    try:
        # Carregar dados
        print(f"Carregando dados para o ano {args.year}...")
        df_votacao, df_locais = load_data(args.year, args.votacao_file)
        print(f"  - Votação: {len(df_votacao)} registros")
        print(f"  - Locais: {len(df_locais)} registros")

        # Aplicar filtros
        if args.municipio_id or args.cargo or args.uf:
            print("Aplicando filtros...")
            df_votacao = apply_filters(
                df_votacao, args.municipio_id, args.cargo, args.uf
            )
            print(f"  - Registros após filtros: {len(df_votacao)}")

        # Processar dados
        print("Processando e fazendo merge dos dados...")
        df_merged = process_data(df_votacao, df_locais)
        print(f"  - Registros após merge: {len(df_merged)}")

        # Calcular indicadores
        print(f"Calculando indicadores para nível: {args.level}...")
        df_final = calculate_indicators(df_merged, args.level)
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

'''
Examples:
python cartpol_app/scripts/results/candidates_vote_neghborhood_results.py \
    --year 2018 --municipio-id 60011 --level municipio --uf RJ \
    --cargo 6 --votacao-file data/votacao_secao_2018_RJ_deputado_federal.csv

python cartpol_app/scripts/results/candidates_vote_neghborhood_results.py \
    --year 2018 --level estado --uf ES \
    --cargo 1 --votacao-file data/votacao_secao_2018_ES_presidente.csv
'''
