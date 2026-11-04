# Les décisions

Ce que les tech leads ont décidé, avec la raison en une ligne. Une décision qui change s'écrit
ici, avec sa date.

## Comment on travaille (31 octobre 2026)

- **Feature branching, sans fork.** Les bénévoles ont l'accès en écriture et poussent leurs
  branches ; `main` est protégée (CI verte, une approbation, merge en squash). Un seul endroit
  où chercher le travail en cours.
- **Commits conventionnels.** Le titre de la pull request devient le commit sur `main`.
- **Un tech lead approuve, ça suffit.** Pour que les relectures ne s'accumulent pas.
- **Relance au 5e jour, issue libérée au 7e.** Personne ne garde une issue sans y toucher.
- **Un seul tableau, « Rescue Atlas », sans dépendances entre issues.** Statut, Palier (P0 MVP,
  P1, P2, Plus tard) et Épopée (celles de la storymap des PO/PM). Simple à suivre.
- **On repart d'un socle vide** : un projet Django et une app Vue tout juste créés. Les premières
  pièces deviennent des issues pour les bénévoles.
- **Les outils arrivent un par un**, chacun par une issue. Le polissage de la CI aussi.

## La carte et les données (2 novembre 2026)

- **On garde la carte actuelle** (code `CartONG/SOSMedDashboard`) : on met ses dépendances à
  jour. Elle marche déjà : c'est moins risqué que de tout refaire.
- **Avant d'y toucher, des tests Playwright** décrivent ce que fait la carte actuelle. Ils
  protègent la mise à jour et serviront aussi à la nouvelle carte.
- **En parallèle, sans pression, une nouvelle carte écrite de zéro**, dans `frontend/`. La pile
  se choisit avec les bénévoles.
- **Le backend Django passe en premier.** Il porte les données, la carte les affiche.
- **Les données d'abord** : on inventorie les sources et leurs accès, et on écrit un jeu de
  données fictif pour coder sans attendre les vraies.
- **Reconstituer le flux, comprendre les difficultés de saisie, choisir ce qui est public** :
  c'est le travail des PM/PO, avec SOS MEDITERRANEE.

## La carte actuelle (4 novembre 2026)

- **On la garde telle quelle au début.** Mise à jour et testée en local le 4 novembre : elle tourne
  avec le jeton Mapbox et le Google Sheet public actuels, sans compte à nous.
- **La licence du code et les comptes perdus (Sheet, Mapbox) ne bloquent rien.**
- **MapLibre quand le besoin arrive** : des fonds en PMTiles, ou la fin du jeton (#21).

## Encore ouvert

- **La pile de la nouvelle carte** : Vue 3 avec Nuxt, avec Vite seul, ou une autre, selon les
  bénévoles. L'app de `frontend/` n'est qu'un point de départ.
