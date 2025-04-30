from django.db.models import Sum
from cartpol_app.models import VotesInNeighborhood, Political, Neighborhood, Votes

def populate_votes_in_neighborhood():
    # Primeiro deleta os registros existentes (opcional)
    VotesInNeighborhood.objects.all().delete()
    
    # Para cada Political
    for politic in Political.objects.all():
        # Agrega votos por bairro usando as relações
        votes_data = (
            Votes.objects
            .filter(political=politic)
            .values(
                'section__neighborhood',  # Agrupa por bairro
                'section__neighborhood__id'
            )
            .annotate(total=Sum('quantity'))
        )
        
        # Cria os registros na tabela VotesInNeighborhood
        bulk_create_list = []
        for item in votes_data:
            bulk_create_list.append(
                VotesInNeighborhood(
                    political=politic,
                    neighborhood_id=item['section__neighborhood__id'],
                    quantity=item['total']
                )
            )
        
        # Bulk create para performance
        if bulk_create_list:
            VotesInNeighborhood.objects.bulk_create(bulk_create_list)


populate_votes_in_neighborhood()
# python3 manage.py shell < cartpol_app/scripts/update_votes_in_neighborhood/index.py