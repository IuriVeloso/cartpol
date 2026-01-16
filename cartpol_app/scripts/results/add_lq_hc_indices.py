import argparse
import os

import pandas as pd


def detect_type_and_level(df):
    """
    Detecta automaticamente o tipo (candidato/partido) e nível
    (município/estado) baseado nas colunas presentes no DataFrame.

    Args:
        df: DataFrame com os dados

    Returns:
        tuple: (tipo, nível) onde tipo é 'candidato' ou 'partido',
               e nível é 'municipio' ou 'estado'
    """
    # Detectar tipo
    if 'nome_candidato' in df.columns or 'nome_politico' in df.columns:
        tipo = 'candidato'
    elif 'sigla_partido' in df.columns or 'nome_partido' in df.columns:
        tipo = 'partido'
    else:
        raise ValueError(
            "Não foi possível detectar o tipo. "
            "Colunas esperadas: nome_candidato/nome_politico (candidato) "
            "ou sigla_partido/nome_partido (partido)"
        )

    # Detectar nível
    if 'bairro' in df.columns:
        nivel = 'municipio'
    else:
        nivel = 'estado'

    return tipo, nivel


def calculate_lq_hc_ci(df, tipo, nivel):
    """
    Calcula os índices LQ, HC e CI para o DataFrame.

    Args:
        df: DataFrame com os dados
        tipo: 'candidato' ou 'partido'
        nivel: 'municipio' ou 'estado'

    Returns:
        DataFrame com as colunas LQ, HC e CI adicionadas
    """
    df = df.copy()

    # Definir nomes das colunas baseado no tipo e nível
    if nivel == 'municipio':
        e_ij_col = 'votos_absolutos_bairro'
        e_i_col = 'votos_totais_bairro'
        e_col = 'TOTAL_VOTOS_MUNICIPIO'
    else:  # nivel == 'estado'
        e_ij_col = 'votos_absolutos_municipio'
        e_i_col = 'votos_totais_municipio'
        e_col = 'TOTAL_VOTOS_ESTADO'

    if tipo == 'candidato':
        e_j_col = 'votos_totais_candidato'
    else:  # tipo == 'partido'
        e_j_col = 'votos_totais_partido'

    # Validar que todas as colunas necessárias existem
    required_cols = [e_ij_col, e_i_col, e_j_col, e_col]
    missing_cols = [
        col for col in required_cols if col not in df.columns
    ]
    if missing_cols:
        available = list(df.columns)
        raise ValueError(
            f"Colunas necessárias não encontradas: {missing_cols}. "
            f"Colunas disponíveis: {available}"
        )

    # Converter para numérico, tratando erros
    df[e_ij_col] = pd.to_numeric(df[e_ij_col], errors='coerce')
    df[e_i_col] = pd.to_numeric(df[e_i_col], errors='coerce')
    df[e_j_col] = pd.to_numeric(df[e_j_col], errors='coerce')
    df[e_col] = pd.to_numeric(df[e_col], errors='coerce')

    # Calcular LQ: LQ = (E_ij / E_i) / (E_j / E)
    # Simplificando: LQ = (E_ij * E) / (E_i * E_j)
    denominator_lq = df[e_i_col] * df[e_j_col]
    df['LQ'] = (df[e_ij_col] * df[e_col]) / denominator_lq
    # Substituir inf e NaN por NaN
    df['LQ'] = df['LQ'].replace([float('inf'), float('-inf')], pd.NA)

    # Calcular HC: HC = E_ij - (E_i * E_j / E)
    expected = (df[e_i_col] * df[e_j_col]) / df[e_col]
    df['HC'] = df[e_ij_col] - expected
    # Substituir inf e NaN por NaN
    df['HC'] = df['HC'].replace([float('inf'), float('-inf')], pd.NA)

    # Calcular CI (Carvalho Index): CI = (V_i / T_V) × (P_i / T_P)
    # Onde: V_i = E_ij, T_V = E_j, P_i = E_i, T_P = E
    df['CI'] = (df[e_ij_col] / df[e_j_col]) * (df[e_i_col] / df[e_col])
    # Substituir inf e NaN por NaN
    df['CI'] = df['CI'].replace([float('inf'), float('-inf')], pd.NA)

    return df


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description='Adiciona os índices LQ, HC e CI aos CSVs de resultados'
    )
    parser.add_argument(
        '--csv-file', type=str, required=True,
        help='Caminho para o arquivo CSV com resultados'
    )
    parser.add_argument(
        '--output', type=str, default=None,
        help='Caminho para salvar o CSV atualizado (padrão: sobrescreve o original)'
    )
    parser.add_argument(
        '--backup', action='store_true',
        help='Criar backup do arquivo original antes de modificar'
    )

    args = parser.parse_args()

    # Validar que o arquivo existe
    if not os.path.exists(args.csv_file):
        raise FileNotFoundError(f"Arquivo não encontrado: {args.csv_file}")

    # Definir arquivo de saída
    output_file = args.output if args.output else args.csv_file

    # Criar backup se solicitado
    if args.backup and not args.output:
        backup_file = args.csv_file + '.backup'
        print(f"Criando backup: {backup_file}")
        import shutil
        shutil.copy2(args.csv_file, backup_file)

    try:
        # Carregar CSV
        print(f"Carregando CSV: {args.csv_file}")
        df = pd.read_csv(args.csv_file)
        print(f"  - Registros carregados: {len(df)}")
        print(f"  - Colunas: {list(df.columns)}")

        # Detectar tipo e nível
        print("Detectando tipo e nível...")
        tipo, nivel = detect_type_and_level(df)
        print(f"  - Tipo detectado: {tipo}")
        print(f"  - Nível detectado: {nivel}")

        # Calcular LQ, HC e CI
        print("Calculando índices LQ, HC e CI...")
        df = calculate_lq_hc_ci(df, tipo, nivel)
        print(f"  - LQ calculado: {df['LQ'].notna().sum()} valores válidos")
        print(f"  - HC calculado: {df['HC'].notna().sum()} valores válidos")
        print(f"  - CI calculado: {df['CI'].notna().sum()} valores válidos")

        # Estatísticas básicas
        if df['LQ'].notna().any():
            lq_min = df['LQ'].min()
            lq_max = df['LQ'].max()
            lq_mean = df['LQ'].mean()
            print(
                f"  - LQ: min={lq_min:.4f}, max={lq_max:.4f}, "
                f"mean={lq_mean:.4f}"
            )
        if df['HC'].notna().any():
            hc_min = df['HC'].min()
            hc_max = df['HC'].max()
            hc_mean = df['HC'].mean()
            print(
                f"  - HC: min={hc_min:.2f}, max={hc_max:.2f}, "
                f"mean={hc_mean:.2f}"
            )
        if df['CI'].notna().any():
            ci_min = df['CI'].min()
            ci_max = df['CI'].max()
            ci_mean = df['CI'].mean()
            print(
                f"  - CI: min={ci_min:.6f}, max={ci_max:.6f}, "
                f"mean={ci_mean:.6f}"
            )

        # Salvar CSV atualizado
        print(f"Salvando CSV atualizado: {output_file}")
        df.to_csv(output_file, index=False)
        print("  - Arquivo salvo com sucesso!")

    except Exception as e:
        print(f"\nErro durante a execução: {e}")
        raise


if __name__ == '__main__':
    main()

# Examples:
# Adicionar LQ e HC a um CSV de candidatos (nível estado)
# python cartpol_app/scripts/results/add_lq_hc_indices.py \
#     --csv-file cartpol_app/scripts/results/script_results/resultado_votacao_estado_2022_1_RJ.csv
#
# Adicionar LQ e HC a um CSV de candidatos (nível município)
# python cartpol_app/scripts/results/add_lq_hc_indices.py \
#     --csv-file cartpol_app/scripts/results/script_results/\
# resultado_votacao_municipio_2018.csv --backup
#
# Adicionar LQ e HC a um CSV de partidos
# python cartpol_app/scripts/results/add_lq_hc_indices.py \
#     --csv-file cartpol_app/scripts/results/script_results/\
# resultado_votacao_partidos_estado_2022.csv \
#     --output cartpol_app/scripts/results/script_results/\
# resultado_votacao_partidos_estado_2022_com_lq_hc.csv
