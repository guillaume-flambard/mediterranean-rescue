# Les vues reçoivent une requête et renvoient une réponse. Ici, une seule vue : elle
# renvoie en JSON les opérations publiées, que la carte (frontend/) affiche.
# Voir le tutoriel, parties 1 et 3 : https://docs.djangoproject.com/fr/6.1/intro/tutorial03/

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .models import Operation

# Les champs envoyés à la carte. Le résumé et l'état de publication restent dans l'admin.
FIELDS = ["id", "kind", "occurred_on", "title", "people", "latitude", "longitude", "source_url"]


# require_GET refuse toute autre méthode (POST, DELETE...) : cette adresse ne fait que lire.
@require_GET
def index(request):
    """Liste des opérations publiées. Adresse : /api/operations/"""
    # filter(published=True) : seules les opérations vérifiées sortent de la base.
    # values(...) : on ne garde que les champs utiles, sous forme de dictionnaires.
    operations = Operation.objects.filter(published=True).values(*FIELDS)
    # JsonResponse attend un dictionnaire ; la liste est donc rangée sous une clé.
    return JsonResponse({"operations": list(operations)})
