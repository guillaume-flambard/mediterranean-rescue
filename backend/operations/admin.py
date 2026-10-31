# L'admin de Django sert d'outil de relecture : on y crée, corrige et publie les
# opérations. Adresse en local : http://127.0.0.1:8000/admin/
# Pour s'y connecter, créer d'abord un compte : uv run manage.py createsuperuser
# Voir le tutoriel, partie 7 : https://docs.djangoproject.com/fr/6.1/intro/tutorial07/

from django.contrib import admin

from .models import Operation


class OperationAdmin(admin.ModelAdmin):
    # Les colonnes de la liste des opérations.
    list_display = ["occurred_on", "kind", "title", "people", "published"]
    # Les filtres dans la colonne de droite.
    list_filter = ["published", "kind"]
    # La barre de recherche cherche dans ces champs.
    search_fields = ["title", "summary"]
    # La navigation par année, mois et jour au-dessus de la liste.
    date_hierarchy = "occurred_on"


# On déclare le modèle à l'admin, avec la configuration ci-dessus.
admin.site.register(Operation, OperationAdmin)
