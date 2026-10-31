# Les adresses de l'application operations. Ce fichier est branché dans config/urls.py
# sous le préfixe api/operations/ (tutoriel, partie 1).

from django.urls import path

from . import views

# Espace de noms : on désigne cette adresse par "operations:index", par exemple dans
# les tests avec reverse("operations:index") (tutoriel, partie 3).
app_name = "operations"
urlpatterns = [
    # /api/operations/
    path("", views.index, name="index"),
]
