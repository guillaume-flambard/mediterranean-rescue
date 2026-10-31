# Les tests de l'application. Pour les lancer : uv run manage.py test
# Django crée une base de test vide, lance chaque test, puis la supprime : vos données
# ne sont jamais touchées. Voir le tutoriel, partie 5 :
# https://docs.djangoproject.com/fr/6.1/intro/tutorial05/

import datetime

from django.test import TestCase
from django.urls import reverse

from .models import Operation


def create_operation(**fields):
    """Crée une opération fictive. Les tests n'utilisent jamais de données réelles."""
    defaults = {
        "kind": Operation.Kind.RESCUE,
        "occurred_on": datetime.date(2026, 1, 12),
        "title": "FICTIF opération",
        "source_url": "https://example.org/fictif",
    }
    return Operation.objects.create(**(defaults | fields))


class OperationIndexViewTests(TestCase):
    def test_lists_published_operations_only(self):
        """Une opération non publiée n'apparaît pas dans l'API."""
        create_operation(title="FICTIF publiée", published=True)
        create_operation(title="FICTIF brouillon")
        response = self.client.get(reverse("operations:index"))
        self.assertEqual(response.status_code, 200)
        titles = [operation["title"] for operation in response.json()["operations"]]
        self.assertEqual(titles, ["FICTIF publiée"])

    def test_unknown_values_stay_empty(self):
        """Un nombre ou une position inconnus restent vides (null), jamais zéro."""
        create_operation(published=True)
        operation = self.client.get(reverse("operations:index")).json()["operations"][0]
        self.assertIsNone(operation["people"])
        self.assertIsNone(operation["latitude"])

    def test_refuses_writes(self):
        """L'API ne fait que lire : un POST est refusé (405)."""
        response = self.client.post(reverse("operations:index"))
        self.assertEqual(response.status_code, 405)
