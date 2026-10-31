# 0002. Un socle minimal, tiré des commandes officielles

Date : 30 octobre 2026. Statut : en vigueur.

## Contexte

Les bénévoles ont tous les niveaux, et beaucoup découvrent Django ou Vue. Un socle qui suit pas à
pas la documentation officielle leur permet de s'appuyer sur les tutoriels, plutôt que sur une
architecture propre au projet.

## Décision

- On repart de zéro avec les commandes officielles, dans l'ordre de la documentation, dernières
  versions au 30/10/2026. Le détail des commandes est dans le [TECHNICAL.md](../../TECHNICAL.md#comment-ce-projet-a-été-créé).
  - Backend : `uv init --bare`, `uv add django` (6.1.2), `django-admin startproject config .`,
    `uv run manage.py startapp operations`, puis le tutoriel Django 6.1 (parties 1, 2, 3, 5 et 7)
    pour le modèle, l'admin, la vue et les tests. uv installe Python et fige les versions
    (`uv.lock`), comme dans les autres projets de Data for Good.
  - Frontend : `pnpm create vue@latest frontend --ts --router --vitest --playwright --eslint
    --prettier --bare` (create-vue 3.24.0, [guide Vue](https://vuejs.org/guide/quick-start.html)),
    puis `pnpm add maplibre-gl` (6.16.0).
- SQLite, la base par défaut de Django. Pas de Docker pour développer.
- Pas de Django REST Framework ni de drf-spectacular : une vue `JsonResponse` suffit pour un
  endpoint, et drf-spectacular 0.30.0 ne déclare pas encore Django 6.1 ni DRF 3.18
  ([README](https://drf-spectacular.readthedocs.io/en/latest/readme.html)). À reprendre quand
  l'API grandira.
- L'admin Django, en français, sert d'outil de relecture : une opération n'est publique que
  cochée « publiée ».
- Pas encore de Pinia, vue-i18n ni TanStack Query : chacun entrera avec le lot qui en a besoin.
- Le code est en anglais ; les commentaires, la documentation et les décisions sont en français,
  la langue des bénévoles. Chaque fichier écrit à la main explique ce qu'il fait.

## Conséquences

- Un bénévole lance le projet avec Python, Node et pnpm, et retrouve la structure des guides
  officiels, commentée en français.
- Ce qui n'y est pas encore (traductions, sources de données, couches) arrive lot par lot, en
  suivant la doc officielle de chaque outil.
- Les paramètres de `settings.py` sont ceux du démarrage rapide (clé `django-insecure`, `DEBUG`) :
  la mise en production (lot L13) suivra la
  [checklist de déploiement](https://docs.djangoproject.com/fr/6.1/howto/deployment/checklist/).
