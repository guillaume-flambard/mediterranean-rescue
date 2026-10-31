# AGENTS.md

Consignes pour les assistants de code (Claude Code, Codex, Copilot, Cursor…) qui travaillent
dans ce dépôt. Ce fichier s'adresse aux outils, pas aux personnes : tout ce qui compte pour elles
est dans [CONTRIBUTING.md](CONTRIBUTING.md), et les règles sont les mêmes.

## Avant d'écrire du code

1. Vérifier que la personne a l'accord de son tech lead pour se servir d'un assistant : le
   projet le demande tant que les règles d'usage ne sont pas écrites. Sinon, le lui dire et
   s'arrêter là.
2. Lire l'issue en entier : le besoin, les critères d'acceptation, le hors-périmètre, la zone de
   fichiers. Le travail s'arrête à cette issue.
3. Lire [CONTRIBUTING.md](CONTRIBUTING.md) (chemin, quatre règles), la liste du modèle de pull
   request (`.github/pull_request_template.md`, la définition de « fini ») et le
   [glossaire](docs/glossaire.md) (les mots du métier, à reprendre dans le code).
4. Si un critère est ambigu ou manque, le dire à la personne et proposer une question pour
   l'issue. Ne pas deviner un besoin métier.

## Où en est le code

Le dépôt part des gabarits officiels ([décision 0004](docs/decisions/0004-demarrer-d-un-socle-vide.md)) :

- `backend/` : le projet Django `config` (`django-admin startproject`) et l'application
  `operations` (`manage.py startapp`), sans modèle ni migration ; un test de fumée.
- `frontend/` : l'app `create-vue` (TypeScript, Router, Vitest, Playwright, ESLint avec Oxlint,
  Prettier), une page d'accueil `src/views/HomeView.vue`, sans données.

Le modèle, l'admin, l'API et la carte arrivent par les issues, dans cet ordre de chemin :

```
admin Django (relecture)  ->  operations.Operation (SQLite)  ->  /api/operations/  ->  type TypeScript  ->  MapLibre
```

## Les règles des données, à suivre dès le premier modèle

- **Une opération** (`Operation`) est une action en mer racontée par SOS MEDITERRANEE. Ses types
  sont stockés en anglais (`rescue`, `transfer`, `medevac`, `incident`, `shipwreck`,
  `dead_missing`) et libellés en français dans l'admin ([glossaire](docs/glossaire.md)).
- **Un champ `published` sera la seule frontière entre brouillon et public.** Toute donnée qui
  sort de l'API passe par `filter(published=True)`.
- **Inconnu.** Un nombre ou une position inconnus valent `null` (`null=True, blank=True`), un
  texte inconnu vaut une chaîne vide. Jamais `0` : zéro personne secourue et un nombre inconnu
  ne disent pas la même chose. Côté TypeScript, ces champs sont `number | null`.
- **Positions.** WGS84, degrés décimaux, dans deux champs `latitude` et `longitude`. Piège :
  MapLibre et GeoJSON attendent `[longitude, latitude]`, dans cet ordre. Une opération sans
  position n'a pas de point sur la carte.
- **Source.** Une adresse de source est obligatoire : toute donnée affichée cite d'où elle vient.
- **Contrat de l'API.** Le type TypeScript décrit exactement le JSON de l'API : changer l'un,
  c'est changer l'autre dans la même pull request.
- **Données disponibles.** Seulement des données fictives, titres préfixés `FICTIF`, dans
  `backend/operations/fixtures/operations/` quand elles existeront. Les vraies sources ne sont
  pas branchées.
- **Sensible.** SOS MEDITERRANEE n'a pas encore décidé du niveau de détail publiable (positions
  exactes, nationalités des personnes secourues). N'ajouter aucun champ de ce genre sans une
  issue validée par les tech leads. Aucune donnée personnelle n'entre dans ce dépôt.

Cette section grandira avec le modèle de données : les tech leads la tiennent à jour.

## Pendant

- Ne toucher que la zone de fichiers de l'issue. Pas de refactor voisin, pas de « tant qu'on y
  est ».
- Écrire au moins un test par critère d'acceptation. Pour un bug, écrire d'abord le test qui le
  reproduit et le voir échouer.
- Le code doit rester lisible par un bénévole qui découvre Django ou Vue : la structure des
  tutoriels officiels, des noms explicites, un commentaire en français qui dit ce que fait chaque
  partie. Pas d'abstraction que l'issue ne demande pas.
- Suivre la doc de la version installée (Django 6.1, Vue 3.5, et MapLibre 6 une fois ajouté).
  N'ajouter aucune dépendance que l'issue ne prévoit pas.
- Structure Django du tutoriel : une application par domaine (`startapp`), vues dans
  `views.py`, adresses dans le `urls.py` de l'application, tests dans `tests.py`, données
  d'exemple dans `fixtures/<application>/`. Structure Vue de `create-vue` : pages dans
  `src/views/`, composants dans `src/components/`, routes dans `src/router/`.
- Faire évoluer la base avec `makemigrations` puis `migrate` ; ne jamais écrire ni modifier une
  migration à la main. Base SQLite ; paquets Python gérés par uv (`uv add`, jamais pip), versions
  figées dans `uv.lock` ; paquets JavaScript gérés par pnpm.
- Code en anglais ; commentaires, docstrings et documentation en français.
- Couleurs et espacements : les jetons de `frontend/src/assets/main.css`.
- Viser une petite PR : environ 300 lignes au plus hors tests.

## Ne jamais

- Mettre une donnée réelle dans le code, les tests, les fixtures, une issue ou un commit : les
  exemples sont fictifs et marqués `FICTIF`. Inconnu reste `null`, jamais zéro.
- Mettre un secret dans Git (les clés vivent dans `.env`).
- Copier du code de CartONG/SOSMedDashboard (sans licence) ; sa carte est un cahier des charges
  ([docs/parite-cartong.md](docs/parite-cartong.md)).
- Appeler un service extérieur depuis la carte (ni Mapbox, ni clé de tuiles). MapLibre seulement.
- Modifier `AGENTS.md`, `.github/`, `.pre-commit-config.yaml` ou `docs/decisions/` sans que
  l'issue le demande : ces fichiers appartiennent aux tech leads.
- Pousser sur `main`, ou merger une pull request.

## Vérifier avant de rendre la main

```sh
cd backend && uv run pre-commit run --all-files \
  && uv run manage.py check && uv run manage.py makemigrations --check --dry-run && uv run manage.py test
cd frontend && pnpm lint && pnpm test:unit --run && pnpm build
```

Tout doit être vert. Ne jamais dire qu'un test passe sans l'avoir lancé.

## Rendre le travail

- Une branche par issue, depuis `main`, nommée `type/numéro-mots-cles`, poussée sur ce dépôt.
  Messages de commit au format des commits conventionnels
  ([CONTRIBUTING.md](CONTRIBUTING.md#les-messages-de-commit)) ; aucune ligne « Co-Authored-By »
  ni signature d'outil.
- Préparer la description de PR avec le modèle (`.github/pull_request_template.md`), et rappeler
  à la personne de cocher la ligne de l'assistant IA, avec le nom de l'outil.
- Résumer à la personne ce qui a changé et pourquoi, pour qu'elle puisse expliquer chaque ligne
  à la relecture : c'est elle qui ouvre la PR, et elle en répond.

## Repères

Où est quoi : le tableau de [TECHNICAL.md](TECHNICAL.md). Décisions : [docs/decisions/](docs/decisions/).
Architecture visée : [docs/guides/03-architecture.md](docs/guides/03-architecture.md).
Travail à prendre : [docs/lots.md](docs/lots.md).
