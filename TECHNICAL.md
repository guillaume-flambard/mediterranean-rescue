# Documentation technique

## La pile

- **Django 6.1** et **SQLite** pour le backend.
- **Vue 3.5**, **Vite** et **TypeScript** pour le frontend.
- **pre-commit**, **ruff**, **ESLint**, **Oxlint**, **Vitest** et **Playwright** pour les
  vérifications.

Le backend est le projet créé par `django-admin startproject`, avec une application `operations`
vide. Le frontend est l'app créée par `create-vue`. Rien d'autre pour l'instant.

## Ce qu'il faut installer

- [uv](https://docs.astral.sh/uv/getting-started/installation/), qui installe Python et les
  paquets du backend.
- Node.js 24.12 ou plus récent, et pnpm.

## Lancer le projet

Deux terminaux. Dans VS Code, la tâche « Lancer le backend et le frontend » fait les deux.

**Le backend**, sur http://127.0.0.1:8000 :

```sh
cd backend
uv sync                            # installe Python et les paquets
uv run manage.py migrate           # crée la base SQLite
uv run manage.py createsuperuser   # ton compte pour l'admin
uv run manage.py runserver
```

L'admin est sur http://127.0.0.1:8000/admin/.

**Le frontend**, sur http://localhost:5173 :

```sh
cd frontend
pnpm install
pnpm dev
```

Installe aussi les contrôles avant commit, une seule fois : `cd backend && uv run pre-commit install`.

## Vérifier avant de pousser

```sh
# Dans backend/
uv run pre-commit run --all-files
uv run manage.py check
uv run manage.py makemigrations --check --dry-run
uv run manage.py test

# Dans frontend/
pnpm lint
pnpm test:unit --run
pnpm build
pnpm test:e2e --project=chromium   # si le changement touche un parcours
```

La CI relance tout cela sur chaque pull request. Dans VS Code : la tâche « Tout vérifier ».

## Modifier le modèle

Après un changement dans `backend/operations/models.py` :

```sh
uv run manage.py makemigrations operations   # la migration, à committer
uv run manage.py migrate
```

## Où est quoi

| Chemin | Rôle |
|---|---|
| `backend/config/` | Les réglages et les adresses du site |
| `backend/operations/` | L'application des opérations : modèles, admin, vues, tests |
| `frontend/src/` | L'app Vue : pages, composants, routes |
| `frontend/e2e/` | Les tests dans un navigateur |
| `data/` | Les données locales, jamais committées |
| `docs/` | Les décisions, la progression des bénévoles, le glossaire |
| `.github/` | CI, modèles d'issue et de pull request |

Code en anglais ; commentaires et documentation en français.
