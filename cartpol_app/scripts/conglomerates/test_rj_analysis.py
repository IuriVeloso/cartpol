"""
Script de teste para análise de concentração política no Rio de Janeiro.

Este script:
1. Lista políticos disponíveis no banco para o município do RJ
2. Executa a análise de concentração para políticos selecionados
3. Salva os resultados em arquivos JSON

Uso:
    python test_rj_analysis.py --political-id 633844 --qe 59154
    python test_rj_analysis.py --list-politicians --county-id 2
    python test_rj_analysis.py --list-counties
"""

import argparse
import json
import os
import sys

# Adicionar diretório raiz ao path
BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, BASE_DIR)

# Configuração do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cartpol.settings')

import django
django.setup()

from django.db.models import Count, Sum
from cartpol_app.models import (County, Political, PoliticalType,
                                VotesInNeighborhood)
from politics_analysis import analyze_political_concentration


def list_counties_with_votes():
    """Lista municípios que possuem votos registrados."""
    counties = (
        VotesInNeighborhood.objects
        .values('neighborhood__county__id', 'neighborhood__county__name')
        .annotate(total_votes=Sum('quantity'), neighborhoods_count=Count('neighborhood', distinct=True))
        .order_by('-total_votes')
    )

    print("\n=== MUNICÍPIOS COM VOTOS REGISTRADOS ===")
    for county in counties[:10]:
        print(f"  ID: {county['neighborhood__county__id']}, "
              f"Nome: {county['neighborhood__county__name']}, "
              f"Votos: {county['total_votes']:,}, "
              f"Bairros: {county['neighborhoods_count']}")

    return list(counties)


def list_politicians_by_county(county_id: int, limit: int = 20):
    """Lista políticos de um município específico."""
    politicians = (
        Political.objects
        .filter(region_id=county_id)
        .select_related('political_party', 'election', 'political_type')
        .annotate(total_votes=Sum('votesinneighborhood__quantity'))
        .order_by('-total_votes')
    )[:limit]

    print(f"\n=== TOP {limit} POLÍTICOS DO MUNICÍPIO (ID: {county_id}) ===")
    for p in politicians:
        print(f"  ID: {p.id}, Nome: {p.name}, Partido: {p.political_party.name}, "
              f"Tipo: {p.political_type.name}, Ano: {p.election.year}, "
              f"Votos: {p.total_votes:,}" if p.total_votes else
              f"  ID: {p.id}, Nome: {p.name}, Partido: {p.political_party.name}, "
              f"Tipo: {p.political_type.name}, Ano: {p.election.year}, Votos: N/A")

    return list(politicians)


def run_analysis_for_politicians(
    politician_ids: list,
    qe: float,
    neighbors_json: str,
    output_dir: str = None
):
    """Executa análise para uma lista de políticos."""

    if output_dir is None:
        output_dir = os.path.dirname(__file__)

    results = []

    for political_id in politician_ids:
        print(f"\n{'#'*60}")
        print(f"# ANALISANDO POLÍTICO ID: {political_id}")
        print(f"{'#'*60}")

        try:
            output_path = os.path.join(
                output_dir,
                f"result_political_{political_id}.json"
            )

            result = analyze_political_concentration(
                political_id=political_id,
                qe=qe,
                neighbors_json_path=neighbors_json,
                output_path=output_path
            )

            results.append({
                'political_id': political_id,
                'success': True,
                'result': result
            })

        except Exception as e:
            print(f"Erro ao analisar político {political_id}: {e}")
            results.append({
                'political_id': political_id,
                'success': False,
                'error': str(e)
            })

    return results


def print_result_summary(results: list):
    """Imprime resumo dos resultados."""
    print("\n" + "="*60)
    print("RESUMO FINAL")
    print("="*60)

    for r in results:
        if r['success']:
            result = r['result']
            print(
                f"\nPolítico: {result['political']['name']} ({result['political']['party']})")
            print(f"  Total de votos: {result['political']['total_votes']:,}")
            print(
                f"  Bairros após filtro: {result['filtering']['neighborhoods_after_filter']}")
            print(f"  Classificação: {result['filtering']['classification']}")
            print(
                f"  Conglomerados: {result['summary']['total_conglomerates']}")
            print(
                f"  Concentração Final: {result['summary']['concentracao_final']:.4f}")
            print(f"  Interpretação: {result['summary']['interpretation']}")
        else:
            print(f"\nPolítico ID {r['political_id']}: ERRO - {r['error']}")


def save_summary(results: list, summary_path: str):
    """Salva resumo em arquivo JSON."""
    summary_data = []
    for r in results:
        if r['success']:
            summary_data.append({
                'political_id': r['political_id'],
                'name': r['result']['political']['name'],
                'party': r['result']['political']['party'],
                'total_votes': r['result']['political']['total_votes'],
                'concentracao_final': r['result']['summary']['concentracao_final'],
                'interpretation': r['result']['summary']['interpretation'],
                'total_conglomerates': r['result']['summary']['total_conglomerates']
            })
        else:
            summary_data.append({
                'political_id': r['political_id'],
                'error': r['error']
            })

    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=2)

    print(f"\n>>> Resumo salvo em: {summary_path}")


def main():
    """Função principal do teste."""
    parser = argparse.ArgumentParser(
        description='Análise de concentração política no Rio de Janeiro',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Listar municípios disponíveis
  python test_rj_analysis.py --list-counties

  # Listar políticos de um município
  python test_rj_analysis.py --list-politicians --county-id 2

  # Analisar um político específico
  python test_rj_analysis.py --political-id 633844 --qe 59154

  # Analisar múltiplos políticos
  python test_rj_analysis.py --political-id 633844 633845 633846 --qe 59154
        """
    )

    # Comandos de listagem
    parser.add_argument('--list-counties', action='store_true',
                        help='Listar municípios com votos registrados')
    parser.add_argument('--list-politicians', action='store_true',
                        help='Listar políticos de um município')
    parser.add_argument('--county-id', type=int, default=2,
                        help='ID do município (padrão: 2 = Rio de Janeiro)')
    parser.add_argument('--limit', type=int, default=30,
                        help='Limite de políticos a listar (padrão: 30)')

    # Parâmetros de análise
    parser.add_argument('--political-id', type=int, nargs='+',
                        help='ID(s) do(s) político(s) a analisar')
    parser.add_argument('--qe', type=float,
                        help='Quociente Eleitoral (obrigatório para análise)')
    parser.add_argument('--neighbors-json', type=str,
                        default=os.path.join(os.path.dirname(
                            __file__), 'resultado.json'),
                        help='Caminho para o arquivo JSON de vizinhança')
    parser.add_argument('--output-dir', type=str,
                        default=os.path.dirname(__file__),
                        help='Diretório para salvar os resultados')

    args = parser.parse_args()

    print("="*60)
    print("ANÁLISE DE CONCENTRAÇÃO POLÍTICA - RIO DE JANEIRO")
    print("="*60)

    # Modo: Listar municípios
    if args.list_counties:
        list_counties_with_votes()
        return

    # Modo: Listar políticos
    if args.list_politicians:
        list_politicians_by_county(args.county_id, limit=args.limit)
        return

    # Modo: Análise
    if args.political_id:
        # Validar Q.E.
        if args.qe is None:
            print(
                "\nERRO: O parâmetro --qe (Quociente Eleitoral) é obrigatório para análise.")
            print("Use: python test_rj_analysis.py --political-id <ID> --qe <VALOR>")
            return

        # Validar arquivo de vizinhança
        if not os.path.exists(args.neighbors_json):
            print(
                f"\nERRO: Arquivo de vizinhança não encontrado: {args.neighbors_json}")
            return

        print(f"\nQuociente Eleitoral: {args.qe:,.2f}")
        print(f"Político(s): {args.political_id}")
        print(f"Arquivo de vizinhança: {args.neighbors_json}")

        # Executar análise
        results = run_analysis_for_politicians(
            politician_ids=args.political_id,
            qe=args.qe,
            neighbors_json=args.neighbors_json,
            output_dir=args.output_dir
        )

        # Mostrar e salvar resumo
        print_result_summary(results)

        summary_path = os.path.join(args.output_dir, 'test_summary.json')
        save_summary(results, summary_path)

        return

    # Nenhum modo especificado - mostrar ajuda
    parser.print_help()


if __name__ == '__main__':
    main()
