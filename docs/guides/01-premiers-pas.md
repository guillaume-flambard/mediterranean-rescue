# Niveau 1 : premiers pas

Ce guide part de zéro : il suppose seulement que uv, Node.js, pnpm et Git sont installés
(versions dans la [documentation technique](../../TECHNICAL.md#ce-quil-faut-installer)).

## 1. Récupérer le projet

```sh
git clone https://github.com/dataforgoodfr/mediterranean-rescue.git
cd mediterranean-rescue
```

## 2. Lancer l'API et la carte

Suivre la section [« Lancer le projet » de la documentation technique](../../TECHNICAL.md#lancer-le-projet). À la fin,
deux terminaux tournent :

- l'API Django sur http://127.0.0.1:8000 ;
- la carte sur http://localhost:5173, avec 4 opérations fictives.

## 3. Publier une opération dans l'admin

1. Ouvrir http://127.0.0.1:8000/admin/ et se connecter avec le compte créé par
   `createsuperuser`.
2. *Opérations*, puis *Ajouter une opération*. Remplir un titre qui commence par `FICTIF`, une
   date, un type, une latitude (par exemple `34.5`), une longitude (`12.8`) et une adresse de
   source (`https://example.org/fictif`).
3. Laisser *publiée* décochée, enregistrer, recharger la carte : rien ne change.
4. Cocher *publiée*, enregistrer, recharger : le point apparaît.

C'est la règle du projet : une personne vérifie la source avant toute publication.

## 4. Installer les contrôles automatiques

```sh
cd backend
uv run pre-commit install
```

Désormais, chaque `git commit` vérifie le style et corrige ce qu'il peut. S'il a corrigé un
fichier, ajoutez-le de nouveau (`git add`) et recommencez le commit.

## 5. Première pull request

1. Choisir une `good first issue`, commenter « Je prends ».
2. Créer sa branche depuis `main` :

   ```sh
   git switch main
   git pull
   git switch -c docs/7-corrige-glossaire
   ```

3. Faire le changement, puis vérifier (commandes dans [TECHNICAL.md](../../TECHNICAL.md#vérifier-avant-de-pousser)).
4. Committer et pousser :

   ```sh
   git add docs/glossaire.md
   git commit -m "Fix the definition of MRCC in the glossary"
   git push -u origin docs/7-corrige-glossaire
   ```

5. Sur GitHub, ouvrir la pull request vers `main` et remplir le modèle.
6. Attendre la relecture, répondre aux commentaires par de nouveaux commits sur la même branche.

## Les commandes Git utiles

| Commande | Ce qu'elle fait |
|---|---|
| `git status` | ce qui a changé et ce qui est prêt à committer |
| `git diff` | le détail des changements |
| `git switch main && git pull` | récupérer le travail des autres |
| `git switch -c type/numero-mots` | créer sa branche |
| `git log --oneline -5` | les cinq derniers commits |

Une erreur, une branche en désordre ? Demandez dans l'issue : un tech lead vous aidera à la
remettre d'aplomb, sans rien perdre.
