#!/bin/sh
# Crée les étiquettes du projet sur GitHub (voir CONTRIBUTING.md). À lancer une fois, par
# un tech lead, depuis la racine du dépôt : sh .github/create-labels.sh
# Il faut l'outil `gh` connecté au compte (https://cli.github.com). --force met à jour
# une étiquette qui existe déjà.
set -e
gh label create "prête" --color 0E8A16 --description "On peut la prendre : besoin, critères et zone sont clairs" --force
gh label create "besoin-spec" --color FBCA04 --description "Le besoin n'est pas encore assez clair" --force
gh label create "bloquée" --color B60205 --description "Attend une réponse ou une autre issue" --force
gh label create "niveau-2" --color 7FC97F --description "Intermédiaire" --force
gh label create "niveau-3" --color 1B7837 --description "Confirmé" --force
gh label create "good first issue" --color 7057FF --description "Première contribution : petite, guidée, sans prérequis" --force
gh label create "front" --color 1B2747 --description "La carte (frontend/)" --force
gh label create "back" --color 5319E7 --description "L'API (backend/)" --force
gh label create "data" --color E83E1B --description "Sources et données" --force
gh label create "docs" --color 0075CA --description "Documentation" --force
gh label create "ci" --color BFD4F2 --description "CI et outillage" --force
gh label create "bug" --color D73A4A --description "Quelque chose ne marche pas" --force
