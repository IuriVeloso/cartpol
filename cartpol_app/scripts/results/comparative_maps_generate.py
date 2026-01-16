import argparse
import os

import geopandas as gpd
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Mapeamento de critérios para colunas
CRITERION_COLUMNS = {
    'votos_absolutos': 'votos_absolutos_municipio',
    'rcan_uesp': 'RCAN_UESP(%)',
    'ruesp_can': 'RUESP_CAN(%)'
}

# Cores padrão para partidos conhecidos
PARTY_COLORS = {
    'PT': '#E31E24',      # Vermelho
    'PSDB': '#005CA9',    # Azul
    'PL': '#00A859',      # Verde
    'PSL': '#FFD700',     # Dourado
    'MDB': '#00CED1',     # Ciano
    'PSOL': '#FF6B00',    # Laranja
    'PDT': '#FFD700',     # Amarelo
    'PCdoB': '#E31E24',   # Vermelho
    'PV': '#00FF00',      # Verde claro
    'REDE': '#00CED1',    # Ciano
    'NOVO': '#FF1493',    # Rosa
    'PODE': '#FF8C00',    # Laranja escuro
    'CIDADANIA': '#FFD700',  # Amarelo
    'PSB': '#FFD700',     # Amarelo
    'PP': '#0000FF',      # Azul
    'REPUBLICANOS': '#0000CD',  # Azul médio
    'UNIÃO': '#1E90FF',   # Azul dodger
    'AVANTE': '#FFA500',  # Laranja
    'SOLIDARIEDADE': '#FF6347',  # Tomate
    'PTB': '#E31E24',     # Vermelho
    'PSC': '#00FF00',     # Verde
    'PSD': '#005CA9',     # Azul
    'DEM': '#005CA9',     # Azul
    'PMN': '#005CA9',     # Azul
    'PHS': '#005CA9',     # Azul
    'PMB': '#FF69B4',     # Rosa
    'PSTU': '#E31E24',    # Vermelho
    'PCO': '#E31E24',     # Vermelho
    'PCB': '#E31E24',     # Vermelho
}

# Mapeamento de número do partido para sigla
PARTY_NUMBER_TO_SIGLA = {
    10: 'REPUBLICANOS',
    11: 'PP',
    12: 'PDT',
    13: 'PT',
    14: 'PTB',
    15: 'MDB',
    16: 'PSTU',
    17: 'PSL',
    18: 'REDE',
    19: 'PODE',
    20: 'PSC',
    21: 'PCB',
    22: 'PL',
    23: 'CIDADANIA',
    25: 'DEM',
    27: 'PMN',
    30: 'NOVO',
    40: 'PSB',
    43: 'PV',
    44: 'UNIÃO',
    45: 'PSDB',
    50: 'PSOL',
    55: 'PSD',
    65: 'PCdoB',
    70: 'AVANTE',
    77: 'SOLIDARIEDADE',
}


def detect_data_type(df):
    """
    Detecta se o DataFrame é de candidatos ou partidos.

    Args:
        df: DataFrame com dados de votação

    Returns:
        str: 'candidato' ou 'partido'
    """
    if 'nome_candidato' in df.columns:
        return 'candidato'
    elif 'sigla_partido' in df.columns:
        return 'partido'
    else:
        raise ValueError(
            "Não foi possível detectar o tipo de dados. "
            "O CSV deve conter 'nome_candidato' (candidatos) ou "
            "'sigla_partido' (partidos)."
        )


def load_shapefile(uf):
    """
    Carrega o shapefile do estado.

    Args:
        uf: Sigla do estado

    Returns:
        GeoDataFrame com o shapefile carregado
    """
    # Tentar primeiro com _Municipios_2024.zip
    shapefile_path = f'data/maps/{uf}_Municipios_2024.zip'
    if not os.path.exists(shapefile_path):
        # Tentar com _UF_2023.zip
        shapefile_path = f'data/maps/{uf}_UF_2023.zip'
        if not os.path.exists(shapefile_path):
            raise FileNotFoundError(
                f"Shapefile não encontrado. Tentou: "
                f"data/maps/{uf}_Municipios_2024.zip e "
                f"data/maps/{uf}_UF_2023.zip"
            )

    print(f"Carregando shapefile: {shapefile_path}")
    gdf = gpd.read_file(f"zip://{shapefile_path}")
    print(f"  - Shapefile carregado: {len(gdf)} features")
    print(f"  - Colunas disponíveis: {list(gdf.columns)[:10]}...")

    return gdf


def merge_data_with_shapefile(gdf, df_data):
    """
    Faz merge dos dados com o shapefile por código do município.

    Args:
        gdf: GeoDataFrame do shapefile
        df_data: DataFrame com dados de votação

    Returns:
        GeoDataFrame merged
    """
    print("Fazendo merge dos dados com shapefile...")

    possible_municipio_name_cols = ['NM_MUN', 'NOME_MUNICIPIO', 'municipio']

    municipio_col = None

    for col in possible_municipio_name_cols:
        if col in gdf.columns:
            municipio_col = col
            break

    if municipio_col is None:
        print(f"  - Colunas disponíveis no shapefile: {list(gdf.columns)}")
        raise ValueError(
            "Não foi possível encontrar coluna de município no shapefile"
        )

    print(f"  - Usando coluna '{municipio_col}' do shapefile")

    # Merge por nome (normalizar para comparação)
    gdf[municipio_col] = (
        gdf[municipio_col].astype(str).str.strip().str.lower()
    )
    # Precisamos do nome do município no df_data
    # Mas winners_df só tem municipio_id, então precisamos buscar o nome
    # Vamos assumir que o CSV original tem o nome do município
    # Por enquanto, vamos tentar fazer merge direto se houver coluna 'municipio'
    if 'municipio' not in df_data.columns:
        raise ValueError(
            "Para merge por nome, é necessário ter coluna 'municipio' no CSV. "
            "Use um CSV que contenha dados completos."
        )
    df_data['municipio'] = (
        df_data['municipio'].astype(str).str.strip().str.lower()
    )

    gdf_merged = gdf.merge(
        df_data,
        left_on=municipio_col,
        right_on='municipio',
        how='left'
    )

    print(f"  - Features após merge: {len(gdf_merged)}")
    print(
        f"  - Features com dados: "
        f"{gdf_merged[gdf_merged['winner_entity'].notna()].shape[0]}"
    )

    return gdf_merged


def assign_colors(entities, data_type, entity_numbers=None):
    """
    Atribui cores aos candidatos/partidos.

    Args:
        entities: Lista de nomes/siglas de candidatos/partidos
        data_type: 'candidato' ou 'partido'
        entity_numbers: Dicionário opcional mapeando entidade -> número do partido

    Returns:
        dict: Mapeamento de entidade para cor
    """
    colors_dict = {}

    if data_type == 'partido':
        # Para partidos, usar cores padrão quando disponível
        # Primeiro, atribuir cores padrão
        for entity in entities:
            if entity in PARTY_COLORS:
                colors_dict[entity] = PARTY_COLORS[entity]

        # Para partidos sem cor padrão, usar paleta automática
        remaining_entities = [e for e in entities if e not in colors_dict]
        if remaining_entities:
            # Usar paleta tab20 que tem 20 cores distintas
            cmap = plt.cm.get_cmap('tab20')
            num_colors = len(remaining_entities)
            colors = [cmap(i) for i in np.linspace(0, 1, num_colors)]

            for i, entity in enumerate(remaining_entities):
                # Converter de RGBA para hex
                rgba = colors[i]
                hex_color = '#{:02x}{:02x}{:02x}'.format(
                    int(rgba[0] * 255),
                    int(rgba[1] * 255),
                    int(rgba[2] * 255)
                )
                colors_dict[entity] = hex_color
    else:
        # Para candidatos, tentar usar cores baseadas no número do partido
        if entity_numbers:
            # Primeiro, tentar obter cor pelo número do partido
            for entity in entities:
                if entity in entity_numbers:
                    party_number = entity_numbers[entity]
                    # Extrair os dois primeiros dígitos do número (código do partido)
                    if pd.notna(party_number):
                        try:
                            # Converter para string e pegar os dois primeiros dígitos
                            number_str = str(int(float(party_number)))
                            if len(number_str) >= 2:
                                party_code = int(number_str[:2])
                                # Buscar sigla do partido pelo número
                                if party_code in PARTY_NUMBER_TO_SIGLA:
                                    party_sigla = PARTY_NUMBER_TO_SIGLA[party_code]
                                    if party_sigla in PARTY_COLORS:
                                        colors_dict[entity] = PARTY_COLORS[party_sigla]
                        except (ValueError, TypeError):
                            pass

        # Para candidatos sem cor baseada em partido, usar paleta automática
        remaining_entities = [e for e in entities if e not in colors_dict]
        if remaining_entities:
            cmap = plt.cm.get_cmap('tab20')
            num_colors = len(remaining_entities)
            colors = [cmap(i) for i in np.linspace(0, 1, num_colors)]

            for i, entity in enumerate(remaining_entities):
                rgba = colors[i]
                hex_color = '#{:02x}{:02x}{:02x}'.format(
                    int(rgba[0] * 255),
                    int(rgba[1] * 255),
                    int(rgba[2] * 255)
                )
                colors_dict[entity] = hex_color

    return colors_dict


def process_comparative_data(df, criterion, entity_list=None):
    """
    Processa dados e identifica vencedores por município.

    Args:
        df: DataFrame com dados de votação
        criterion: Critério de comparação ('votos_absolutos', 'rcan_uesp', 'ruesp_can')
        entity_list: Lista opcional de candidatos/partidos para comparar

    Returns:
        tuple: (DataFrame com vencedores por município, dict mapeando entidade -> número)
    """
    # Validar critério
    if criterion not in CRITERION_COLUMNS:
        raise ValueError(
            f"Critério inválido: {criterion}. "
            f"Use: {list(CRITERION_COLUMNS.keys())}"
        )

    criterion_col = CRITERION_COLUMNS[criterion]
    if criterion_col not in df.columns:
        raise ValueError(
            f"Coluna '{criterion_col}' não encontrada no CSV. "
            f"Colunas disponíveis: {list(df.columns)}"
        )

    # Detectar tipo de dados
    data_type = detect_data_type(df)
    entity_col = 'nome_candidato' if data_type == 'candidato' else 'sigla_partido'

    print(f"Tipo de dados detectado: {data_type}")
    print(f"Critério: {criterion} (coluna: {criterion_col})")

    # Filtrar por lista de entidades se fornecida
    if entity_list:
        print(f"Filtrando por {len(entity_list)} entidades...")
        df = df[df[entity_col].isin(entity_list)]
        if df.empty:
            raise ValueError(
                f"Nenhuma das entidades fornecidas foi encontrada no CSV. "
                f"Entidades disponíveis: {df[entity_col].unique()[:10]}"
            )
    else:
        print("Usando todas as entidades do CSV")

    # Para cada município, encontrar o vencedor
    winners = []
    municipios = df['municipio_id'].unique()

    print(f"Processando {len(municipios)} municípios...")
    for municipio_id in municipios:
        df_municipio = df[df['municipio_id'] == municipio_id].copy()

        # Remover linhas com valores NaN no critério
        df_municipio = df_municipio[df_municipio[criterion_col].notna()]

        if df_municipio.empty:
            # Se não há dados válidos para este município, pular
            continue

        # Encontrar máximo do critério
        max_value = df_municipio[criterion_col].max()

        # Verificar se max_value não é NaN
        if pd.isna(max_value):
            continue

        # Identificar entidade(s) com esse valor
        winners_df_municipio = df_municipio[
            df_municipio[criterion_col] == max_value
        ]

        # Em caso de empate, escolher o primeiro
        winner_entity = winners_df_municipio[entity_col].iloc[0]
        winner_value = max_value

        # Obter informações do município (nome, UF, etc)
        municipio_info = df_municipio.iloc[0]
        municipio_name = municipio_info.get('municipio', '')
        municipio_uf = municipio_info.get('UF', '')

        winners.append({
            'municipio_id': municipio_id,
            'municipio': municipio_name,
            'UF': municipio_uf,
            'winner_entity': winner_entity,
            'winner_value': winner_value
        })

    winners_df = pd.DataFrame(winners)
    print(f"  - Vencedores identificados: {len(winners_df)} municípios")

    # Estatísticas
    entity_counts = winners_df['winner_entity'].value_counts()
    print("\nDistribuição de vencedores:")
    for entity, count in entity_counts.head(10).items():
        print(f"  - {entity}: {count} municípios")

    # Criar mapeamento de entidade -> número do partido (apenas para candidatos)
    entity_numbers = {}
    if data_type == 'candidato' and 'numero_candidato' in df.columns:
        # Para cada entidade vencedora, buscar o número do candidato
        for entity in winners_df['winner_entity'].unique():
            entity_data = df[df[entity_col] == entity]
            if not entity_data.empty:
                # Pegar o primeiro número encontrado (deve ser o mesmo para o mesmo candidato)
                numero = entity_data['numero_candidato'].iloc[0]
                entity_numbers[entity] = numero

    return winners_df, entity_numbers


def generate_comparative_map(
    gdf_merged, winners_df, colors_dict, criterion, year, output_path, data_type
):
    """
    Gera mapa comparativo com cores por vencedor.

    Args:
        gdf_merged: GeoDataFrame merged com shapefile e dados
        winners_df: DataFrame com vencedores por município
        colors_dict: Dicionário de entidade -> cor
        criterion: Critério usado para comparação
        year: Ano da eleição
        output_path: Caminho para salvar o mapa
        data_type: 'candidato' ou 'partido'
    """
    print(f"Gerando mapa comparativo: {criterion}...")

    # Criar coluna de cor no GeoDataFrame
    gdf_plot = gdf_merged.copy()
    gdf_plot['plot_color'] = gdf_plot['winner_entity'].map(colors_dict)

    # Criar figura
    _, ax = plt.subplots(1, 1, figsize=(14, 12))

    # Plotar features sem dados em cinza
    gdf_no_data = gdf_plot[gdf_plot['plot_color'].isna()]
    if not gdf_no_data.empty:
        gdf_no_data.plot(
            ax=ax, color='lightgray', edgecolor='white',
            linewidth=0.5
        )

    # Plotar features com dados (agrupar por cor para melhor performance)
    gdf_with_data = gdf_plot[gdf_plot['plot_color'].notna()]
    if not gdf_with_data.empty:
        # Plotar cada cor separadamente
        for color in gdf_with_data['plot_color'].unique():
            gdf_color = gdf_with_data[gdf_with_data['plot_color'] == color]
            gdf_color.plot(
                ax=ax, color=color, edgecolor='white',
                linewidth=0.5
            )

    # Criar legenda
    patches = []

    # Ordenar por frequência (mais vencedores primeiro)
    entity_counts = winners_df['winner_entity'].value_counts()
    for entity in entity_counts.index:
        if entity in colors_dict:
            patch = mpatches.Patch(
                color=colors_dict[entity], label=entity
            )
            patches.append(patch)

    # Adicionar legenda
    ax.legend(
        handles=patches, loc='upper left', bbox_to_anchor=(1.02, 1),
        fontsize=10, frameon=True, fancybox=True, shadow=True
    )

    # Configurar título
    criterion_names = {
        'votos_absolutos': 'Votos Absolutos',
        'rcan_uesp': 'RCAN_UESP',
        'ruesp_can': 'RUESP_CAN'
    }
    criterion_display = criterion_names.get(criterion, criterion.upper())
    data_type_display = 'Candidatos' if data_type == 'candidato' else 'Partidos'

    title = (
        f'Mapa Comparativo - {criterion_display}\n'
        f'{data_type_display} - {year}'
    )
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)

    # Remover eixos
    ax.axis('off')

    # Ajustar layout
    plt.tight_layout()

    # Salvar
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  - Mapa salvo em: {output_path}")


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description='Gera mapas comparativos mostrando qual candidato/partido '
                    'teve melhor desempenho em cada município'
    )
    parser.add_argument(
        '--csv-file', type=str, required=True,
        help='Caminho para o arquivo CSV com resultados de votação'
    )
    parser.add_argument(
        '--criterion', type=str, required=True,
        choices=['votos_absolutos', 'rcan_uesp', 'ruesp_can'],
        help='Critério de comparação: votos_absolutos, rcan_uesp ou ruesp_can'
    )
    parser.add_argument(
        '--entities', type=str, default=None,
        help='Lista de candidatos/partidos separados por vírgula (opcional). '
             'Se não fornecido, usa todos do CSV.'
    )
    parser.add_argument(
        '--uf', type=str, required=True,
        help='Sigla do estado'
    )
    parser.add_argument(
        '--year', type=int, required=True,
        help='Ano da eleição'
    )
    parser.add_argument(
        '--output-dir', type=str,
        default='cartpol_app/scripts/results/script_results',
        help='Diretório para salvar os mapas'
    )

    args = parser.parse_args()

    # Validar arquivo CSV
    if not os.path.exists(args.csv_file):
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {args.csv_file}")

    # Processar lista de entidades se fornecida
    entity_list = None
    if args.entities:
        entity_list = [e.strip() for e in args.entities.split(',')]
        print(f"Entidades especificadas: {len(entity_list)}")

    # Criar diretório de saída
    os.makedirs(args.output_dir, exist_ok=True)

    try:
        # Carregar dados do CSV
        print(f"\nCarregando dados do CSV: {args.csv_file}")
        df_data = pd.read_csv(args.csv_file)
        print(f"  - Registros carregados: {len(df_data)}")

        if df_data.empty:
            raise ValueError("O arquivo CSV está vazio")

        # Validar colunas necessárias
        required_cols = ['municipio_id']
        missing_cols = [
            col for col in required_cols if col not in df_data.columns]
        if missing_cols:
            raise ValueError(
                f"Colunas obrigatórias não encontradas no CSV: {missing_cols}. "
                f"Colunas disponíveis: {list(df_data.columns)}"
            )

        # Detectar tipo de dados
        data_type = detect_data_type(df_data)
        print(f"  - Tipo detectado: {data_type}")

        # Validar entidades fornecidas
        if entity_list:
            entity_col = 'nome_candidato' if data_type == 'candidato' else 'sigla_partido'
            available_entities = df_data[entity_col].unique()
            invalid_entities = [
                e for e in entity_list if e not in available_entities]
            if invalid_entities:
                print(
                    f"  ⚠ Aviso: Algumas entidades não foram encontradas: {invalid_entities[:5]}")
                print(
                    f"  Entidades disponíveis (primeiras 10): {list(available_entities[:10])}")

        # Processar dados comparativos
        winners_df, entity_numbers = process_comparative_data(
            df_data, args.criterion, entity_list
        )

        if len(winners_df) == 0:
            raise ValueError(
                "Nenhum vencedor foi identificado. Verifique os dados e filtros."
            )

        # Atribuir cores
        unique_entities = winners_df['winner_entity'].unique()
        colors_dict = assign_colors(unique_entities, data_type, entity_numbers)
        print(f"  - Cores atribuídas a {len(colors_dict)} entidades")
        if entity_numbers:
            print(
                f"  - Cores baseadas em números de partido: "
                f"{len(entity_numbers)} candidatos"
            )

        # Carregar shapefile
        gdf = load_shapefile(args.uf)

        # Fazer merge
        gdf_merged = merge_data_with_shapefile(gdf, winners_df)

        # Verificar se há dados suficientes após merge
        features_with_data = gdf_merged[gdf_merged['winner_entity'].notna(
        )].shape[0]
        if features_with_data == 0:
            raise ValueError(
                "Nenhum dado foi encontrado após o merge com o shapefile. "
                "Verifique se os códigos/nomes dos municípios estão corretos."
            )

        # Gerar nome do arquivo de saída
        criterion_safe = args.criterion.replace('_', '_')
        output_filename = f'mapa_comparativo_{criterion_safe}_{args.year}.png'
        output_path = os.path.join(args.output_dir, output_filename)

        # Gerar mapa
        generate_comparative_map(
            gdf_merged, winners_df, colors_dict, args.criterion,
            args.year, output_path, data_type
        )

        print(f"\n✓ Mapa comparativo gerado com sucesso!")
        print(f"  - Arquivo: {output_path}")
        print(f"  - Municípios mapeados: {features_with_data}")

    except FileNotFoundError as e:
        print(f"\n✗ Erro: Arquivo não encontrado - {e}")
        raise
    except ValueError as e:
        print(f"\n✗ Erro de validação: {e}")
        raise
    except Exception as e:
        print(f"\n✗ Erro durante a geração do mapa: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == '__main__':
    main()

# Examples:
# python cartpol_app/scripts/results/comparative_maps_generate.py \
#     --csv-file cartpol_app/scripts/results/script_results/resultado_votacao_partidos_estado_2022.csv \
#     --criterion votos_absolutos --uf RJ --year 2022 
#     --entities "PL,PT"

# python cartpol_app/scripts/results/comparative_maps_generate.py \
#     --csv-file cartpol_app/scripts/results/script_results/resultado_votacao_estado_2022_1_RJ.csv \
#     --criterion rcan_uesp \
#     --entities "LUIZ INÁCIO LULA DA SILVA,JAIR MESSIAS BOLSONARO" \
#     --uf RJ --year 2022
