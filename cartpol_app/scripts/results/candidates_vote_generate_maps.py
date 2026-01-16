import argparse
import os
import re

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd


def get_municipio_name(df_data, municipio_id):
    """
    Obtém o nome do município a partir do municipio_id.

    Args:
        df_data: DataFrame com dados de votação
        municipio_id: ID do município

    Returns:
        Nome do município
    """
    municipio_data = df_data[df_data['municipio_id'] == municipio_id]
    if municipio_data.empty:
        raise ValueError(
            f"Município com ID {municipio_id} não encontrado nos dados"
        )
    municipio_name = municipio_data['municipio'].iloc[0]
    return municipio_name


def load_shapefile(level, uf, municipio_name=None):
    """
    Carrega o shapefile apropriado baseado no nível de análise.

    Args:
        level: Nível de análise ('municipio' ou 'estado')
        uf: Sigla do estado
        municipio_name: Nome do município (obrigatório para nível município)

    Returns:
        GeoDataFrame com o shapefile carregado
    """
    if level == 'municipio':
        if municipio_name is None:
            raise ValueError(
                "Nome do município é obrigatório para nível município"
            )
        shapefile_path = f'data/maps/{municipio_name}.zip'
    elif level == 'estado':
        shapefile_path = f'data/maps/{uf}_Municipios_2024.zip'
    else:
        raise ValueError(f"Nível inválido: {level}")

    if not os.path.exists(shapefile_path):
        raise FileNotFoundError(
            f"Shapefile não encontrado: {shapefile_path}"
        )

    print(f"Carregando shapefile: {shapefile_path}")
    gdf = gpd.read_file(f"zip://{shapefile_path}")
    print(f"  - Shapefile carregado: {len(gdf)} features")
    print(f"  - Colunas disponíveis: {list(gdf.columns)[:10]}...")

    return gdf


def normalize_name_for_match(name):
    """
    Normaliza nome para fazer match (remove acentos, espaços, etc).

    Args:
        name: Nome a normalizar

    Returns:
        Nome normalizado
    """
    if pd.isna(name):
        return ''
    # Converter para string, remover espaços extras, converter para minúsculas
    name = str(name).strip().lower()
    # Remover caracteres especiais (manter apenas letras e números)
    name = re.sub(r'[^a-z0-9]', '', name)
    return name


def merge_data_with_shapefile(gdf, df_data, level):
    """
    Faz merge dos dados com o shapefile.

    Args:
        gdf: GeoDataFrame do shapefile
        df_data: DataFrame com dados de votação
        level: Nível de análise ('municipio' ou 'estado')

    Returns:
        GeoDataFrame merged
    """
    print(f"Fazendo merge dos dados com shapefile (nível: {level})...")

    if level == 'municipio':
        # Para nível município, fazer merge por nome do bairro
        # Tentar diferentes colunas possíveis no shapefile
        possible_bairro_cols = [
            'NM_BAIRRO', 'NOME', 'BAIRRO', 'bairro', 'nome',
            'NM_DIST', 'DISTRITO', 'distrito'
        ]

        bairro_col = None
        for col in possible_bairro_cols:
            if col in gdf.columns:
                bairro_col = col
                break

        if bairro_col is None:
            print(f"  - Colunas disponíveis no shapefile: {list(gdf.columns)}")
            raise ValueError(
                "Não foi possível encontrar coluna de bairro no shapefile"
            )

        print(f"  - Usando coluna '{bairro_col}' do shapefile")
        print(f"  - Dados únicos no shapefile: {gdf[bairro_col].nunique()}")

        # Normalizar nomes para fazer match
        gdf['bairro_normalized'] = gdf[bairro_col].apply(
            normalize_name_for_match
        )
        df_data['bairro_normalized'] = df_data['bairro'].apply(
            normalize_name_for_match
        )

        # Fazer merge
        gdf_merged = gdf.merge(
            df_data,
            left_on='bairro_normalized',
            right_on='bairro_normalized',
            how='left'
        )

        # Remover coluna auxiliar
        gdf_merged = gdf_merged.drop(columns=['bairro_normalized'])

    elif level == 'estado':
        # Para nível estado, fazer merge por código do município
        # Tentar diferentes colunas possíveis no shapefile
        possible_municipio_cols = [
            'NM_MUN', 'CD_MUNICIPIO', 'COD_MUN', 'municipio_id',
            'CD_GEOCODM', 'GEOCODIGO'
        ]

        municipio_col = None
        for col in possible_municipio_cols:
            if col in gdf.columns:
                municipio_col = col
                break

        if municipio_col is None:
            print(f"  - Colunas disponíveis no shapefile: {list(gdf.columns)}")
            raise ValueError(
                "Não foi possível encontrar coluna de município no shapefile"
            )

        print(f"  - Usando coluna '{municipio_col}' do shapefile")

        # Converter para mesmo tipo
        gdf[municipio_col] = gdf[municipio_col].astype(
            str).str.strip().str.lower()
        df_data['municipio'] = (
            df_data['municipio'].astype(str).str.strip().str.lower()
        )

        print(gdf[municipio_col].astype(str))
        print(df_data['municipio'].astype(str))

        # Fazer merge
        gdf_merged = gdf.merge(
            df_data,
            left_on=municipio_col,
            right_on='municipio',
            how='left'
        )

    else:
        raise ValueError(f"Nível inválido: {level}")

    print(f"  - Features após merge: {len(gdf_merged)}")
    print(
        f"  - Features com dados: "
        f"{gdf_merged[gdf_merged['nome_candidato'].notna()].shape[0]}"
    )

    return gdf_merged


def generate_map(
    gdf_merged, indicator_column, candidate_name, indicator_name,
    year, output_path, level, cmap='YlOrRd', label_suffix='(%)'
):
    """
    Gera um mapa individual com matplotlib.

    Args:
        gdf_merged: GeoDataFrame merged com dados
        indicator_column: Nome da coluna com o indicador
        candidate_name: Nome do candidato
        indicator_name: Nome do indicador para título
        year: Ano da eleição
        output_path: Caminho para salvar o mapa
        level: Nível de análise
        cmap: Colormap a ser usado (padrão: 'YlOrRd')
        label_suffix: Sufixo para a legenda (padrão: '(%)')
    """
    print(f"Gerando mapa: {indicator_name}...")

    # Filtrar apenas features com dados
    gdf_plot = gdf_merged.copy()

    # Criar figura
    _, ax = plt.subplots(1, 1, figsize=(12, 10))

    # Preparar dados para plotagem
    gdf_plot['plot_value'] = pd.to_numeric(
        gdf_plot[indicator_column], errors='coerce'
    )

    # Plotar features sem dados em cinza
    gdf_no_data = gdf_plot[gdf_plot['plot_value'].isna()]
    if not gdf_no_data.empty:
        gdf_no_data.plot(
            ax=ax, color='lightgray', edgecolor='white',
            linewidth=0.5, label='Sem dados'
        )

    # Plotar features com dados
    gdf_with_data = gdf_plot[gdf_plot['plot_value'].notna()]
    if not gdf_with_data.empty:
        gdf_with_data.plot(
            ax=ax, column='plot_value', cmap=cmap,
            edgecolor='white', linewidth=0.5,
            legend=True, legend_kwds={
                'label': f'{indicator_name} {label_suffix}',
                'orientation': 'horizontal',
                'pad': 0.02,
                'shrink': 0.8
            }
        )

    # Configurar título
    level_text = 'Bairros' if level == 'municipio' else 'Municípios'
    title = (
        f'{indicator_name} - {candidate_name}\n'
        f'{level_text} - {year}'
    )
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

    # Remover eixos
    ax.axis('off')

    # Ajustar layout
    plt.tight_layout()

    # Salvar
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  - Mapa salvo em: {output_path}")


def generate_maps(
    csv_file, candidate_name, level, municipio_id, uf, year,
    output_dir='cartpol_app/scripts/results/script_results'
):
    """
    Orquestra a geração dos mapas.

    Args:
        csv_file: Caminho para o arquivo CSV com resultados
        candidate_name: Nome do candidato
        level: Nível de análise ('municipio' ou 'estado')
        municipio_id: ID do município (obrigatório para nível município)
        uf: Sigla do estado
        year: Ano da eleição
        output_dir: Diretório para salvar os mapas
    """
    # Criar diretório se não existir
    os.makedirs(output_dir, exist_ok=True)

    # Carregar dados do CSV
    print(f"Carregando dados do CSV: {csv_file}")
    df_data = pd.read_csv(csv_file)
    print(f"  - Registros carregados: {len(df_data)}")

    # Filtrar por candidato
    df_candidate = df_data[df_data['nome_candidato'] == candidate_name]
    if df_candidate.empty:
        available = df_data['nome_candidato'].unique()[:10]
        raise ValueError(
            f"Candidato '{candidate_name}' não encontrado nos dados. "
            f"Candidatos disponíveis: {available}"
        )
    print(f"  - Registros do candidato: {len(df_candidate)}")

    # Obter nome do município se necessário
    municipio_name = None
    if level == 'municipio':
        if municipio_id is None:
            raise ValueError(
                "municipio_id é obrigatório para nível município"
            )
        municipio_name = get_municipio_name(df_data, municipio_id)
        print(f"  - Município: {municipio_name}")

    # Carregar shapefile
    gdf = load_shapefile(level, uf, municipio_name)

    # Fazer merge
    gdf_merged = merge_data_with_shapefile(gdf, df_candidate, level)

    # Normalizar nome do candidato para nome de arquivo
    candidate_name_safe = re.sub(r'[^a-zA-Z0-9]', '_', candidate_name)

    # Verificar se as colunas LQ e HC existem
    has_lq = 'LQ' in gdf_merged.columns
    has_hc = 'HC' in gdf_merged.columns

    print("\nVerificando colunas disponíveis após merge:")
    cols_preview = list(gdf_merged.columns)[:15]
    print(f"  - Colunas no gdf_merged: {cols_preview}...")
    print(f"  - LQ disponível: {has_lq}")
    print(f"  - HC disponível: {has_hc}")

    if has_lq:
        lq_count = gdf_merged['LQ'].notna().sum()
        print(f"  - Valores LQ não-nulos: {lq_count}")
    if has_hc:
        hc_count = gdf_merged['HC'].notna().sum()
        print(f"  - Valores HC não-nulos: {hc_count}")

    # Gerar os mapas
    maps_generated = []

    # Mapa RCAN_UESP
    rcan_uesp_path = os.path.join(
        output_dir,
        f'mapa_RCAN_UESP_{candidate_name_safe}_{year}.png'
    )
    generate_map(
        gdf_merged, 'RCAN_UESP(%)', candidate_name,
        'RCAN_UESP', year, rcan_uesp_path, level
    )
    maps_generated.append(rcan_uesp_path)

    # Mapa RUESP_CAN
    ruesp_can_path = os.path.join(
        output_dir,
        f'mapa_RUESP_CAN_{candidate_name_safe}_{year}.png'
    )
    generate_map(
        gdf_merged, 'RUESP_CAN(%)', candidate_name,
        'RUESP_CAN', year, ruesp_can_path, level
    )
    maps_generated.append(ruesp_can_path)

    # Mapa LQ (se disponível)
    if has_lq:
        lq_path = os.path.join(
            output_dir,
            f'mapa_LQ_{candidate_name_safe}_{year}.png'
        )
        generate_map(
            gdf_merged, 'LQ', candidate_name,
            'LQ (Location Quotient)', year, lq_path, level,
            cmap='RdYlGn', label_suffix=''
        )
        maps_generated.append(lq_path)

    # Mapa HC (se disponível)
    if has_hc:
        hc_path = os.path.join(
            output_dir,
            f'mapa_HC_{candidate_name_safe}_{year}.png'
        )
        generate_map(
            gdf_merged, 'HC', candidate_name,
            'HC (Horizontal Cluster)', year, hc_path, level,
            cmap='RdBu', label_suffix=''
        )
        maps_generated.append(hc_path)

    print("\nMapas gerados com sucesso:")
    for map_path in maps_generated:
        print(f"  - {map_path}")

    return maps_generated


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description='Gera mapas temáticos com indicadores de votação'
    )
    parser.add_argument(
        '--csv-file', type=str, required=True,
        help='Caminho para o arquivo CSV com resultados de votação'
    )
    parser.add_argument(
        '--candidate-name', type=str, required=True,
        help='Nome do candidato para gerar os mapas'
    )
    parser.add_argument(
        '--level', type=str, choices=['municipio', 'estado'], required=True,
        help='Nível de análise: municipio ou estado'
    )
    parser.add_argument(
        '--municipio-id', type=int, default=None,
        help='ID do município (obrigatório para nível município)'
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

    # Validação: municipio_id obrigatório para nível município
    if args.level == 'municipio' and args.municipio_id is None:
        parser.error(
            "--municipio-id é obrigatório quando --level=municipio"
        )

    try:
        generate_maps(
            args.csv_file, args.candidate_name, args.level,
            args.municipio_id, args.uf, args.year, args.output_dir
        )
        print("\nGeração de mapas concluída com sucesso!")
    except Exception as e:
        print(f"\nErro durante a geração de mapas: {e}")
        raise


if __name__ == '__main__':
    main()

'''
Examples:
python cartpol_app/scripts/results/candidates_vote_generate_maps.py \
    --csv-file cartpol_app/scripts/results/script_results/resultado_votacao_estado_2022_1_ES.csv \
    --candidate-name "LUIZ INÁCIO LULA DA SILVA" --level estado --uf ES --year 2022
    
python cartpol_app/scripts/results/candidates_vote_generate_maps.py \
    --csv-file cartpol_app/scripts/results/script_results/resultado_votacao_municipio_2018.csv \
    --candidate-name "NOME DO CANDIDATO" --level municipio --municipio-id 60011 --uf RJ --year 2018
    
'''
