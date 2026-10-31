# Les tests de l'application. Pour les lancer : uv run manage.py test
# Django crée une base de test vide, lance chaque test, puis la supprime : tes données ne sont
# jamais touchées. Voir le tutoriel, partie 5 :
# https://docs.djangoproject.com/fr/6.1/intro/tutorial05/

from django.test import TestCase


class SmokeTests(TestCase):
    def test_admin_login_page_answers(self):
        """Le projet démarre : la page de connexion de l'admin répond."""
        response = self.client.get("/admin/login/")
        self.assertEqual(response.status_code, 200)
