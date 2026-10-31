# Niveau 2 : un champ de bout en bout

Exercice : ajouter le nom du navire à une opération, de la base de données jusqu'à la carte.
Faites-le dans une branche d'essai (`git switch -c essai/navire`), que vous ne pousserez pas :
le vrai travail viendra d'une issue.

Le chemin d'une donnée, dans l'ordre où on le modifie :

```
models.py  ->  migration  ->  admin.py  ->  views.py  ->  tests.py
                                                |
operations.ts  <-  (JSON de /api/operations/)  <-
      |
OperationsMap.vue
```

## 1. Le modèle : `backend/operations/models.py`

Ajouter le champ dans la classe `Operation`, sous `title` :

```python
    # Le navire qui a mené l'opération. Vide si on ne le sait pas.
    vessel = models.CharField("navire", max_length=120, blank=True)
```

`blank=True` : le champ peut rester vide. Pour du texte, Django stocke alors une chaîne vide.

## 2. La migration

Une migration est le fichier qui dit à la base comment changer ses tables. Elle s'écrit toute
seule, on ne la modifie jamais à la main :

```sh
cd backend
uv run manage.py makemigrations operations   # écrit operations/migrations/0002_....py
uv run manage.py migrate                     # l'applique à votre base locale
```

La migration est à committer avec le reste.

## 3. L'admin : `backend/operations/admin.py`

Ajouter `"vessel"` à `list_display` pour voir la colonne dans la liste. Le formulaire d'édition
montre le nouveau champ tout seul.

## 4. L'API : `backend/operations/views.py`

Ajouter `"vessel"` à la liste `FIELDS`. Ouvrir http://127.0.0.1:8000/api/operations/ : chaque
opération a maintenant une clé `vessel`.

## 5. Le test : `backend/operations/tests.py`

Un critère, un test. Par exemple « l'API renvoie le nom du navire » :

```python
    def test_lists_the_vessel(self):
        """L'API renvoie le nom du navire."""
        create_operation(vessel="FICTIF Navire", published=True)
        operation = self.client.get(reverse("operations:index")).json()["operations"][0]
        self.assertEqual(operation["vessel"], "FICTIF Navire")
```

Lancer `uv run manage.py test` : le test passe. Essayez de retirer `"vessel"` de `FIELDS` et
relancez : il échoue. Un test qui ne peut pas échouer ne protège rien.

## 6. Le type côté carte : `frontend/src/operations.ts`

Le type `Operation` décrit exactement le JSON de l'API. Ajouter :

```ts
  vessel: string
```

`pnpm build` vérifie les types : si un fichier utilise mal le nouveau champ, la construction
échoue avec l'endroit exact.

## 7. L'affichage : `frontend/src/components/`

Pour l'exercice, ajouter `vessel: operation.vessel` dans les `properties` du point (fonction
`toPoints` de `operations.ts`), puis l'afficher où l'issue le demande. Écrire le test Vitest qui
va avec dans `frontend/src/__tests__/operations.spec.ts`.

## 8. Vérifier et nettoyer

Lancer toutes les vérifications ([TECHNICAL.md](../../TECHNICAL.md#vérifier-avant-de-pousser)).
Puis abandonner la branche d'essai :

```sh
git switch main
git branch -D essai/navire
cd backend && uv run manage.py migrate operations 0001   # remet votre base comme avant
```

Vous connaissez maintenant le chemin complet. Les issues `niveau-2` le suivent presque toutes.
