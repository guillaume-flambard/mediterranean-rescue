# 0004. Démarrer d'un socle vide

Date : 31 octobre 2026. Statut : en vigueur. Complète la [décision 0002](0002-socle-minimal-officiel.md).

## Contexte

Le premier socle allait déjà de bout en bout : un modèle `Operation` et sa migration, des données
fictives, l'admin de relecture, une vue JSON, une carte MapLibre, un bandeau, le contour des
terres et un test dans le navigateur. Il prouvait que la pile tenait.

Mais il ne laissait presque rien de simple à faire. Un bénévole qui arrive trouvait une carte qui
marche, et des issues qui demandaient déjà de comprendre tout le chemin d'une donnée. Les
premières pièces, celles qui apprennent le projet, étaient faites.

## Décision

- Le code repart des gabarits officiels, sans rien de plus : `django-admin startproject` et
  `manage.py startapp operations` pour le backend, `create-vue` pour le frontend, avec les mêmes
  options qu'en [0002](0002-socle-minimal-officiel.md). `operations/models.py` n'a pas encore de
  modèle, et il n'y a aucune migration à part `__init__.py`.
- Tout l'outillage reste : CI, pre-commit, modèles d'issue et de pull request, relecteurs,
  étiquettes, réglages de VS Code, documentation et décisions.
- Le premier socle est gardé sur la branche `reference/socle-prototype`. Les tech leads s'en
  servent pour écrire les premières issues et pour aider à la relecture ; ce n'est pas du code à
  recopier.
- Chaque pièce du premier socle devient une issue, de la `good first issue` au `niveau-3` : le
  modèle et sa migration, les données fictives, l'admin, l'API, la carte, le bandeau, le contour
  des terres, le test dans le navigateur, le guide « un champ de bout en bout ».
- Les outils et les robots au-delà de la CI et de pre-commit arrivent de la même façon : une
  issue chacun, que des bénévoles peuvent prendre. Améliorer la CI est aussi du travail pour les
  bénévoles.

## Conséquences

- Les premières issues sont de vraies portes d'entrée : petites, guidées, et chacune fait avancer
  la carte.
- La carte n'affiche rien tant que ces issues ne sont pas mergées. Le README le dit.
- Le test dans le navigateur ne lance pas encore l'API : elle le rejoindra avec la première page
  qui lit des données.
- Les choix de [0001](0001-reecrire-en-vue-sans-le-code-cartong.md) et de
  [0002](0002-socle-minimal-officiel.md) restent la cible : Vue, MapLibre sans service extérieur,
  Django et son admin, SQLite, aucune ligne de code CartONG.
