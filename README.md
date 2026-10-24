# Mediterranée Rescue : POC de cartographie historique

Contribution expérimentale construite sur le [dépôt Data for Good](https://github.com/dataforgoodfr/mediterranean-rescue). Le besoin métier, les données et le lien avec la carte CartONG restent à confirmer avec l’équipe. Ce fork n’est pas un produit officiel de SOS MEDITERRANEE.

## Essayer la carte

Depuis la racine du dépôt :

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory web
```

Ouvrir http://127.0.0.1:8765/. On peut également ouvrir directement `web/index.html` dans un navigateur. Aucune installation, clé ou connexion Internet nécessaire à l’exécution. Le serveur doit rester lié à 127.0.0.1 pour cet usage local.

La carte affiche **six événements entièrement fictifs** : les dates, positions, navires et effectifs sont inventés. Les filtres date et navire mettent à jour la carte et le journal. Cliquer sur un point ou un événement affiche son détail. Les boutons de zoom se centrent sur la sélection ; Vue complète rétablit le cadre méditerranéen. La liste donne un accès clavier aux mêmes informations.

## Importer et exporter

Voir [le contrat de données](web/DATA.md) et [l’exemple JSON](web/exemple-import.json). Le POC accepte uniquement des exemples fictifs explicitement marqués. Il ne faut pas changer cette étiquette pour faire passer des données réelles pour fictives. Une intégration réelle nécessite un contrat approuvé avec l’association.

L’import remplace le jeu complet après validation. En cas d’erreur, le jeu précédent reste affiché. Limites : 2 Mio et 2 000 événements. Aucun fichier n’est envoyé ; rien n’est stocké après rechargement. Exporter la sélection télécharge un JSON, en conservant l’étiquette fictive. Restaurer la démo annule les lectures de fichier encore en cours et rétablit les six exemples.

## Vérifier

Node 24 ou plus récent :

```sh
node --test web/model.test.cjs web/app.test.cjs
node --check web/app.js
```

Les tests couvrent validation, calendriers, bornes, doublons, URL, filtres, états vides, import atomique, restauration pendant une lecture, focus et lancement d’export. Les tests d’interface utilisent un DOM minimal et ne remplacent pas une recette navigateur.

Recette manuelle : filtrer Navire B (2 événements, 89 personnes fictives), sélectionner un événement, vérifier sa fiche, choisir une période vide, restaurer ; importer le JSON fourni puis un JSON invalide ; exporter et recharger. Vérifier aussi le confort sur téléphone avant tout usage public.

## Sources et limites

Fond [Natural Earth](https://www.naturalearthdata.com/about/terms-of-use/), domaine public, résolution 1:110m. Voir web/PROVENANCE.md. Projection équirectangulaire simplifiée, destinée à une vue historique. Pas de routes, frontières maritimes, position courante, suivi AIS ou aide à la navigation. Le fond est trop grossier pour l’analyse côtière. Les libellés géographiques sont indicatifs. Les liens externes ne sont chargés que si l’utilisateur les ouvre.

L’[existant CartONG](https://www.cartong.org/en/projet/mapping-for-sos-mediterranee-sea-rescues/) doit être étudié avant toute décision de migration. Aucun besoin d’IA n’est présumé.

La base Python et les workflows hérités sont conservés. Le nom `13_pollution_eau` dans pyproject.toml et le parcours Poetry/py310 dans tox.ini proviennent du template ; ils ne sont pas la configuration de ce POC statique. Aucun service n’a été déployé.

## Base Python héritée

# Template DataForGood

This file will become your README and also the index of your
documentation.

# Contributing


## Installation

- [Installation de Python](#installation-de-python)

Ce projet utilise [uv](https://docs.astral.sh/uv/) pour la gestion des dépendances Python. Il est préréquis pour l'installation de ce projet.

Une fois installé, il suffit de lancer la commande suivante pour installer la version de Python adéquate, créer un environnement virtuel et installer les dépendances du projet.

```bash
uv sync
```

A l'usage, si vous utilisez VSCode, l'environnement virtuel sera automatiquement activé lorsque vous ouvrirez le projet. Sinon, il suffit de l'activer manuellement avec la commande suivante :

```bash
source .venv/bin/activate
```

Ou alors, utilisez la commande `uv run ...` (au lieu de `python ...`) pour lancer un script Python. Par exemple:

```bash
uv run pipelines/run.py run build_database
```


## Lancer les precommit-hook localement

[Installer les precommit](https://pre-commit.com/)

    pre-commit run --all-files

## Utiliser Tox pour tester votre code

    tox -vv
