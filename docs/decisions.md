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
- **Un tableau à plusieurs colonnes, pas de dépendances entre issues.** Simple à suivre.
- **On repart d'un socle vide** : un projet Django et une app Vue tout juste créés. Les premières
  pièces deviennent des issues pour les bénévoles. L'ancien prototype reste sur la branche
  `reference/socle-prototype`, comme exemple seulement.
- **Les outils arrivent un par un**, chacun par une issue. Le polissage de la CI aussi.
- **L'IA, pas à pas.** Les guides n'en parlent pas. Les règles d'usage s'écriront avec Data for
  Good et les PM/PO ; en attendant, on demande à son tech lead.

## La carte et les données (2 novembre 2026)

- **On garde la carte actuelle** (code `CartONG/SOSMedDashboard`) : on met ses dépendances à
  jour, puis on passe de mapbox-gl à MapLibre. Elle marche déjà ; c'est moins risqué que de tout
  refaire, et MapLibre est libre, sans jeton.
- **Avant d'y toucher, des tests Playwright** décrivent ce que fait la carte actuelle. Ils
  protègent la mise à jour et serviront aussi à la nouvelle carte.
- **En parallèle, sans pression, une nouvelle carte écrite de zéro**, dans `frontend/`. La pile
  se choisit avec les bénévoles.
- **Le backend Django passe en premier.** Il porte les données, la carte les affiche.
- **Les données d'abord** : on inventorie les sources et leurs accès, et on écrit un jeu de
  données fictif pour coder sans attendre les vraies.
- **Reconstituer le flux, comprendre les difficultés de saisie, choisir ce qui est public** :
  c'est le travail des PM/PO, avec SOS MEDITERRANEE.

## Encore ouvert

- **Le code de la carte actuelle n'a pas de licence.** Il faut l'accord de CartONG ou de
  SOS MEDITERRANEE pour le modifier ici, et décider où il vivra.
- **La carte actuelle dépend de comptes qu'on n'a plus.** Son Google Sheet et son compte Mapbox
  (jeton et style) étaient liés au compte d'une personne qui ne s'occupe plus du projet
  (appris le 2 novembre). Proposition à valider : faire passer en premier une nouvelle carte
  MapLibre qui reprend toutes les fonctions de l'actuelle, sans jeton ni compte personnel, et
  garder les tests Playwright pour décrire ces fonctions tant que la carte tourne.
- **La pile de la nouvelle carte** : Vue 3 avec Vite, ou Nuxt.
- **Les règles d'usage de l'IA.**
