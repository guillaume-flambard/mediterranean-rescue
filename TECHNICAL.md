# Documentation technique

Tout ce qu'il faut pour faire tourner le projet et y contribuer. La présentation du projet est
dans le [README](README.md) ; le chemin d'une contribution dans [CONTRIBUTING.md](CONTRIBUTING.md).

## La pile

- **Django 6.1** et **SQLite** : l'API (`/api/operations/`) et l'admin de relecture.
- **Vue 3.5**, **Vite** et **TypeScript** : l'app de la carte.
- **MapLibre GL** : la carte, sans service extérieur.
- **pre-commit**, **ruff**, **ESLint**, **Vitest**, **Playwright** : les vérifications.

## Ce qu'il faut installer

- **uv**, qui installe Python et les paquets du backend ([installer uv](https://docs.astral.sh/uv/getting-started/installation/)).
  Vérifier avec `uv --version`. Pas besoin d'installer Python à la main : uv s'en charge.
- **Node.js 24.12 ou plus récent** et **pnpm**. Vérifier avec `node --version` et `pnpm --version`.

## Lancer le projet

Avec VS Code, la tâche « Lancer l'API et la carte » (menu Terminal, « Exécuter la tâche… »)
fait les deux d'un clic, une fois l'installation ci-dessous faite.

Deux terminaux : un pour l'API Django, un pour la carte.

### Terminal 1 : l'API Django (http://127.0.0.1:8000)

```sh
cd backend

# 1. Installer Python et les paquets, aux versions exactes de uv.lock, dans un dossier
#    .venv propre au projet. Une seule fois (puis après chaque changement de pyproject.toml).
uv sync

# 2. `uv run` lance une commande avec le Python du projet, sans rien activer.

# 3. Créer la base SQLite (backend/db.sqlite3) et ses tables.
uv run manage.py migrate

# 4. Charger les opérations fictives d'entraînement (jamais de données réelles).
uv run manage.py loaddata operations/fictional_operations

# 5. Créer votre compte pour l'admin (nom, e-mail, mot de passe).
uv run manage.py createsuperuser

# 6. Démarrer le serveur de développement.
uv run manage.py runserver
```

Ensuite :

- http://127.0.0.1:8000/api/operations/ renvoie les opérations publiées en JSON ;
- http://127.0.0.1:8000/admin/ permet de relire, corriger et publier les opérations.

### Terminal 2 : la carte (http://localhost:5173)

```sh
cd frontend
pnpm install   # installe les paquets, une seule fois
pnpm dev       # démarre la carte
```

Le port 8000 est déjà pris ? Lancer `uv run manage.py runserver 8001`, puis la carte avec
`API_TARGET=http://127.0.0.1:8001 pnpm dev`. Le port 5173 est pris par une autre application ?
Les tests Playwright la réutiliseraient sans prévenir : les lancer alors comme la CI, avec
`CI=1 API_TARGET=http://127.0.0.1:8001 pnpm test:e2e --project=chromium` (après `pnpm build`).

## Où est quoi

| Chemin | Rôle |
|---|---|
| `backend/` | Le projet Django, créé par `django-admin startproject config .` |
| `backend/config/settings.py` | Les réglages : applications installées, base SQLite, langue, fuseau horaire. |
| `backend/config/urls.py` | Les adresses du site : `/api/operations/` et `/admin/`. |
| `backend/operations/` | L'application, créée par `uv run manage.py startapp operations`. |
| `backend/operations/models.py` | Le modèle `Operation` : la table des opérations. |
| `backend/operations/admin.py` | L'admin : relecture et publication. |
| `backend/operations/views.py` | La vue qui renvoie les opérations publiées en JSON. |
| `backend/operations/tests.py` | Les tests (`uv run manage.py test`). |
| `backend/operations/fixtures/operations/` | Les données fictives d'entraînement. |
| `backend/pyproject.toml` | Les paquets Python du backend ; `uv.lock` fige leurs versions exactes. |
| `frontend/` | L'app Vue, créée par `pnpm create vue@latest`. |
| `frontend/src/views/MapView.vue` | La page de la carte : charge les opérations et les passe aux composants. |
| `frontend/src/components/StatusBanner.vue` | Le bandeau : titre et état du chargement. |
| `frontend/src/components/OperationsMap.vue` | La carte MapLibre et ses points. |
| `frontend/src/operations.ts` | Lecture de l'API et conversion des opérations en points. |
| `frontend/src/assets/main.css` | Les jetons de design (couleurs SOS MEDITERRANEE). |
| `frontend/public/land.geojson` | Le contour des terres (Natural Earth, domaine public). |
| `docs/guides/` | Le guide des bénévoles et les guides par niveau. |
| `docs/equipe.md` | Pour les tech leads et les PM/PO : issue prête, étiquettes, relecture. |
| `docs/glossaire.md` | Les mots du métier et leur nom dans le code. |
| `docs/decisions/` | Les décisions du projet, une par fichier. |
| `docs/` | Aussi : cahier de parité avec CartONG, lots. |
| `.github/` | Modèles d'issue et de pull request, CI, relecteurs, bannière du README. |
| `.pre-commit-config.yaml` | Les contrôles lancés à chaque commit. |
| `.vscode/` | Extensions conseillées et tâches en un clic pour VS Code (facultatif). |
| `README.md` | La présentation du projet. |
| `TECHNICAL.md` | Ce fichier : installation, structure, commandes. |
| `CONTRIBUTING.md` | Comment passer d'une issue à une pull request mergée. |
| `AGENTS.md` | Les consignes pour les assistants de code IA (inutile si vous n'en utilisez pas). |

## Vérifier avant de pousser

Dans VS Code, la tâche « Tout vérifier » lance tout. Sinon :

```sh
# Dans backend/
uv run pre-commit run --all-files                   # style et fichiers
uv run manage.py check
uv run manage.py makemigrations --check --dry-run   # rien ne doit s'afficher
uv run manage.py test

# Dans frontend/
pnpm lint
pnpm test:unit --run
pnpm build
pnpm test:e2e --project=chromium   # si le changement touche un parcours ; l'API doit tourner
```

La CI de GitHub relance tout cela sur chaque pull request.

## Modifier le modèle

Après tout changement dans `backend/operations/models.py`, deux commandes (tutoriel Django,
[partie 2](https://docs.djangoproject.com/fr/6.1/intro/tutorial02/)) :

```sh
uv run manage.py makemigrations operations   # écrit la migration, à committer
uv run manage.py migrate                     # l'applique à votre base
```

## Comment ce projet a été créé

Uniquement des commandes officielles, dans l'ordre de leur documentation, le 30 octobre 2026.
Le reste a été écrit à la main en suivant les tutoriels.

**Backend** ([uv](https://docs.astral.sh/uv/guides/projects/),
[tutoriel](https://docs.djangoproject.com/fr/6.1/intro/tutorial01/)) :

```sh
mkdir backend && cd backend
uv init --bare                                # le projet Python (pyproject.toml)
uv add django                                 # Django 6.1.2
uv run django-admin startproject config .
uv run manage.py startapp operations
# écriture de models.py, admin.py, views.py, urls.py, tests.py
uv run manage.py makemigrations operations
uv run manage.py sqlmigrate operations 0001
uv run manage.py check
uv run manage.py migrate
uv run manage.py test
uv add --dev pre-commit                       # les contrôles avant commit
```

**Frontend** ([guide Vue](https://vuejs.org/guide/quick-start.html),
[MapLibre](https://maplibre.org/maplibre-gl-js/docs/)) :

```sh
pnpm create vue@latest frontend --ts --router --vitest --playwright --eslint --prettier --bare
cd frontend
pnpm install
pnpm add maplibre-gl
```

## Versions

Django 6.1.2 sur Python 3.14 (3.12 au minimum), géré par uv, SQLite. Vue 3.5, Vite 8, Vue Router 5, TypeScript 6,
MapLibre GL 6.16, Vitest 4, Playwright, ESLint 10 avec Oxlint, Prettier. Vérifiées le
30 octobre 2026.

## Règles

Les quatre règles du projet sont en tête de [CONTRIBUTING.md](CONTRIBUTING.md#quatre-règles).
Code en anglais ; commentaires, documentation et décisions en français.
