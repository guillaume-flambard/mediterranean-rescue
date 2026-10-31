# Niveau 3 : l'architecture

## Ce qui se passe quand on ouvre la carte

```
Navigateur (http://localhost:5173)
  |  1. Vite sert l'app Vue
  v
frontend/src/main.ts -> router/ -> views/MapView.vue
  |  2. MapView demande les opérations (operations.ts, fetchOperations), puis les passe à
  |     components/StatusBanner.vue (le bandeau) et components/OperationsMap.vue (la carte)
  v
GET /api/operations/  -- Vite renvoie /api vers Django (vite.config.ts, proxy) -->
  |
  v
backend/config/urls.py -> operations/urls.py -> operations/views.py (index)
  |  3. la vue lit les opérations publiées
  v
operations/models.py (Operation) -> SQLite (backend/db.sqlite3)
  |
  v
JSON { "operations": [...] } -> OperationsMap : toPoints() -> GeoJSON -> MapLibre dessine les points
```

En production, le front construit (`pnpm build`) sera servi avec l'API : ce sera le lot L13.

## Les principes

- **Les guides officiels d'abord.** La structure est celle du tutoriel Django et de
  `create-vue`. Avant d'ajouter une bibliothèque, vérifier que la doc officielle ne couvre pas
  déjà le besoin ([décision 0002](../decisions/0002-socle-minimal-officiel.md)).
- **Une application Django par domaine.** `operations` aujourd'hui. Une nouvelle notion du
  métier (navires, sources) devient une nouvelle application (`uv run manage.py startapp`),
  nommée avec les mots du [glossaire](../glossaire.md).
- **L'API est la frontière.** Le front ne connaît que le JSON. Le type TypeScript
  (`operations.ts`) décrit ce JSON exactement : tout changement de l'API change ce type dans la
  même pull request.
- **Rien n'est public sans relecture.** Le champ `published` et l'admin Django portent cette
  règle. Une nouvelle donnée affichée suit le même chemin.
- **Inconnu reste vide.** `null` en base et en JSON, jamais `0`.
- **La carte n'appelle aucun service extérieur.** Le fond de carte est servi par l'app.
- **Un composant par partie de l'écran.** La page charge les données ; chaque partie (bandeau,
  carte, et bientôt fiche, légende) a son composant. Deux issues en parallèle touchent ainsi
  des fichiers différents.

## Les décisions

Chaque choix qui engage le projet est écrit dans [docs/decisions/](../decisions/), une décision
par fichier numéroté : le contexte, la décision, ses conséquences. On ne réécrit pas une
décision prise : on en écrit une nouvelle qui la remplace, et on le dit dans l'ancienne.

Proposer une décision : ouvrir une pull request avec le fichier suivant
(`000N-titre-court.md`), statut « proposée ». Les tech leads la discutent dans la PR.

## Où grandira le projet

Le découpage en lots est dans [docs/lots.md](../lots.md). Les plus gros chantiers à venir :
les sources de données et leur fraîcheur, la position des navires, les fonds de carte libres,
les langues.
