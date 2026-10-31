# Niveau 1 : premiers pas

Ce guide part de zéro : il suppose seulement que uv, Node.js, pnpm et Git sont installés
(versions dans la [documentation technique](../../TECHNICAL.md#ce-quil-faut-installer)).

## 1. Récupérer le projet

```sh
git clone https://github.com/dataforgoodfr/mediterranean-rescue.git
cd mediterranean-rescue
```

## 2. Lancer le backend et le frontend

Suivre la section [« Lancer le projet » de la documentation technique](../../TECHNICAL.md#lancer-le-projet). À la fin,
deux terminaux tournent :

- Django sur http://127.0.0.1:8000 ;
- l'app Vue sur http://localhost:5173, avec la page d'accueil qui annonce la carte.

Il n'y a pas encore de carte ni de données : c'est normal, elles arrivent par les premières
issues ([pourquoi](../decisions/0004-demarrer-d-un-socle-vide.md)).

## 3. Ouvrir l'admin

Ouvrir http://127.0.0.1:8000/admin/ et se connecter avec le compte créé par `createsuperuser`.
L'admin ne montre encore que les comptes et les groupes. Quand le modèle des opérations sera là,
c'est ici qu'une personne relira chaque opération avant de la publier.

## 4. Installer les contrôles automatiques

```sh
cd backend
uv run pre-commit install
```

Désormais, chaque `git commit` vérifie le style et corrige ce qu'il peut. S'il a corrigé un
fichier, ajoute-le de nouveau (`git add`) et recommence le commit.

## 5. Première pull request

1. Choisir une `good first issue`, commenter « Je prends ».
2. Créer sa branche depuis `main` :

   ```sh
   git switch main
   git pull
   git switch -c docs/7-corrige-glossaire
   ```

3. Faire le changement, puis vérifier (commandes dans [TECHNICAL.md](../../TECHNICAL.md#vérifier-avant-de-pousser)).
4. Committer et pousser la branche sur le dépôt :

   ```sh
   git add docs/glossaire.md
   git commit -m "docs: corrige la définition du MRCC"
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
| `git switch -c type/numero-mots-cles` | créer sa branche |
| `git log --oneline -5` | les cinq derniers commits |

Une erreur, une branche en désordre ? Demande dans l'issue : un tech lead t'aidera à la remettre
d'aplomb, sans rien perdre.
