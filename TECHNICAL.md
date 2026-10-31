# Documentation technique

Tout ce qu'il faut pour faire tourner le projet et y contribuer. La présentation du projet est
dans le [README](README.md) ; le chemin d'une contribution dans [CONTRIBUTING.md](CONTRIBUTING.md).

## Où en est le code

Le dépôt part des gabarits officiels, sans rien de plus
([décision 0004](docs/decisions/0004-demarrer-d-un-socle-vide.md)) :

- le backend est le projet Django créé par `django-admin startproject`, avec une application
  `operations` vide, créée par `manage.py startapp` : pas encore de modèle ni de migration ;
- le frontend est l'app créée par `create-vue`, avec une page d'accueil qui annonce la carte ;
- l'outillage est en place : pre-commit, CI, modèles d'issue et de pull request.

Le modèle des opérations, l'admin de relecture, l'API, la carte et ses tests arrivent par les
premières issues. La cible est décrite dans le [guide d'architecture](docs/guides/03-architecture.md).

## La pile

- **Django 6.1** et **SQLite** : l'API et l'admin de relecture (à venir).
- **Vue 3.5**, **Vite** et **TypeScript** : l'app de la carte.
- **MapLibre GL** : la carte, sans service extérieur (à ajouter avec l'issue de la carte).
- **pre-commit**, **ruff**, **ESLint**, **Oxlint**, **Vitest**, **Playwright** : les
  vérifications.

## Ce qu'il faut installer

- **uv**, qui installe Python et les paquets du backend ([installer uv](https://docs.astral.sh/uv/getting-started/installation/)).
  Vérifier avec `uv --version`. Pas besoin d'installer Python à la main : uv s'en charge.
- **Node.js 24.12 ou plus récent** et **pnpm**. Vérifier avec `node --version` et `pnpm --version`.

## Lancer le projet

Avec VS Code, la tâche « Lancer le backend et le frontend » (menu Terminal, « Exécuter la
tâche… ») fait les deux d'un clic, une fois l'installation ci-dessous faite.

Deux terminaux : un pour Django, un pour l'app Vue.

### Terminal 1 : le backend Django (http://127.0.0.1:8000)

```sh
cd backend

# 1. Installer Python et les paquets, aux versions exactes de uv.lock, dans un dossier
#    .venv propre au projet. Une seule fois (puis après chaque changement de pyproject.toml).
uv sync

# 2. `uv run` lance une commande avec le Python du projet, sans rien activer.

# 3. Créer la base SQLite (backend/db.sqlite3) et les tables fournies par Django.
uv run manage.py migrate

# 4. Créer ton compte pour l'admin (nom, e-mail, mot de passe).
uv run manage.py createsuperuser

# 5. Démarrer le serveur de développement.
uv run manage.py runserver
```

Ensuite, http://127.0.0.1:8000/admin/ ouvre l'admin de Django. Il ne montre encore que les
comptes et les groupes : les opérations y entreront avec leur modèle.

### Terminal 2 : le frontend (http://localhost:5173)

```sh
cd frontend
pnpm install   # installe les paquets, une seule fois
pnpm dev       # démarre l'app
```

La page d'accueil annonce la carte. Le port 5173 est pris par une autre application ? Les tests
Playwright la réutiliseraient sans prévenir : les lancer alors comme la CI, avec
`CI=1 pnpm test:e2e --project=chromium` (après `pnpm build`).

## Où est quoi

| Chemin | Rôle |
|---|---|
| `backend/` | Le projet Django, créé par `django-admin startproject config .` |
| `backend/config/settings.py` | Les réglages : applications installées, base SQLite, langue, fuseau horaire. |
| `backend/config/urls.py` | Les adresses du site : pour l'instant `/admin/`. |
| `backend/operations/` | L'application des opérations, créée par `uv run manage.py startapp operations`. |
| `backend/operations/models.py` | Les modèles : vide pour l'instant. |
| `backend/operations/tests.py` | Les tests (`uv run manage.py test`). |
| `backend/pyproject.toml` | Les paquets Python du backend ; `uv.lock` fige leurs versions exactes. |
| `frontend/` | L'app Vue, créée par `pnpm create vue@latest`. |
| `frontend/src/views/HomeView.vue` | La page d'accueil. |
| `frontend/src/router/index.ts` | Les routes : quelle page pour quelle adresse. |
| `frontend/src/assets/main.css` | Les jetons de design (couleurs SOS MEDITERRANEE, espacements). |
| `frontend/src/__tests__/` | Les tests unitaires (`pnpm test:unit`). |
| `frontend/e2e/` | Les tests dans un vrai navigateur (`pnpm test:e2e`). |
| `data/` | Les données locales, jamais committées. |
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

## Vérifier avant de pousser

Dans VS Code, la tâche « Tout vérifier » lance tout. Sinon :

```sh
# Dans backend/
uv run pre-commit run --all-files                   # style et fichiers
uv run manage.py check
uv run manage.py makemigrations --check --dry-run   # doit dire « No changes detected »
uv run manage.py test

# Dans frontend/
pnpm lint
pnpm test:unit --run
pnpm build                          # vérifie aussi les types
pnpm test:e2e --project=chromium    # si le changement touche un parcours
```

La CI de GitHub relance tout cela sur chaque pull request. Une pull request peut s'ouvrir en
brouillon avec des tests encore rouges ; seul le merge demande une CI verte.

## Branches, commits et `main`

Le projet suit le **feature branching** : une branche par issue, créée depuis `main`, nommée
`type/numéro-mots-cles` (par exemple `feat/12-fiche-operation`), poussée sur ce dépôt, puis une
pull request vers `main`. Les messages de commit suivent les commits
conventionnels (`feat:`, `fix:`, `docs:`…). `main` est protégée : CI verte, une approbation d'un
tech lead, merge en squash. Le détail et les exemples sont dans
[CONTRIBUTING.md](CONTRIBUTING.md#le-modèle--une-branche-par-issue).

## Modifier le modèle

Après tout changement dans `backend/operations/models.py`, deux commandes (tutoriel Django,
[partie 2](https://docs.djangoproject.com/fr/6.1/intro/tutorial02/)) :

```sh
uv run manage.py makemigrations operations   # écrit la migration, à committer
uv run manage.py migrate                     # l'applique à ta base
```

## Comment ce projet a été créé

Uniquement des commandes officielles, dans l'ordre de leur documentation. Le reste (commentaires
en français, réglages de langue et de fuseau, page d'accueil, tests) a été écrit à la main en
suivant les tutoriels.

**Backend** ([uv](https://docs.astral.sh/uv/guides/projects/),
[tutoriel](https://docs.djangoproject.com/fr/6.1/intro/tutorial01/)) :

```sh
mkdir backend && cd backend
uv init --bare                                # le projet Python (pyproject.toml)
uv add django                                 # Django 6.1.2
uv run django-admin startproject config .
uv run manage.py startapp operations
uv add --dev pre-commit                       # les contrôles avant commit
```

**Frontend** ([guide Vue](https://vuejs.org/guide/quick-start.html)) :

```sh
pnpm create vue@latest frontend --ts --router --vitest --playwright --eslint --prettier --bare
cd frontend
pnpm install
```

`create-vue` 3.24.0 ajoute Oxlint avec ESLint. Le `package.json` garde des versions un peu plus
récentes d'Oxlint, d'eslint-plugin-vue et de Prettier que celles du gabarit.

## Versions

Django 6.1.2 sur Python 3.14 (3.12 au minimum), géré par uv, SQLite. Vue 3.5, Vite 8, Vue Router 5,
TypeScript 6, Vitest 4, Playwright, ESLint 10 avec Oxlint, Prettier. Vérifiées le 31 octobre 2026.

## Règles

Les quatre règles du projet sont en tête de [CONTRIBUTING.md](CONTRIBUTING.md#quatre-règles).
Code en anglais ; commentaires, documentation et décisions en français.
