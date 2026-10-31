# Niveau 3 : l'architecture visée

Ce guide décrit la cible. Le code part des gabarits officiels
([décision 0004](../decisions/0004-demarrer-d-un-socle-vide.md)) : les fichiers marqués « à
venir » n'existent pas encore, chacun arrive par une issue.

## Ce qui se passera quand on ouvrira la carte

```
Navigateur (http://localhost:5173)
  |  1. Vite sert l'app Vue
  v
frontend/src/main.ts -> router/ -> views/ (la page de la carte, à venir)
  |  2. La page demande les opérations à l'API, puis les passe à ses composants :
  |     le bandeau, la carte MapLibre, plus tard la fiche et la légende (à venir)
  v
GET /api/operations/  -- en développement, Vite renvoie /api vers Django (à venir) -->
  |
  v
backend/config/urls.py -> operations/urls.py -> operations/views.py (à venir)
  |  3. La vue lit les opérations publiées
  v
operations/models.py (Operation, à venir) -> SQLite (backend/db.sqlite3)
  |
  v
JSON { "operations": [...] } -> points GeoJSON -> MapLibre dessine les points
```

En production, le front construit (`pnpm build`) sera servi avec l'API : ce sera le lot L13.

## Les principes

- **Les guides officiels d'abord.** La structure est celle du tutoriel Django et de
  `create-vue`. Avant d'ajouter une bibliothèque, vérifier que la doc officielle ne couvre pas
  déjà le besoin ([décision 0002](../decisions/0002-socle-minimal-officiel.md)).
- **Une application Django par domaine.** `operations` d'abord. Une nouvelle notion du métier
  (navires, sources) deviendra une nouvelle application (`uv run manage.py startapp`), nommée
  avec les mots du [glossaire](../glossaire.md).
- **L'API est la frontière.** Le front ne connaît que le JSON. Un type TypeScript décrira ce JSON
  exactement : tout changement de l'API change ce type dans la même pull request.
- **Rien n'est public sans relecture.** Un champ `published` et l'admin Django porteront cette
  règle. Toute donnée affichée suivra le même chemin.
- **Inconnu reste vide.** `null` en base et en JSON, jamais `0`.
- **La carte n'appelle aucun service extérieur.** Le fond de carte sera servi par l'app.
- **Un composant par partie de l'écran.** La page charge les données ; chaque partie (bandeau,
  carte, fiche, légende) a son composant. Deux issues en parallèle touchent ainsi des fichiers
  différents.

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
