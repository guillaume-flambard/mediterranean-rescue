# Pour les tech leads et les PM/PO

Ce que les bénévoles n'ont pas besoin de lire : comment on prépare le travail et comment on le
relit. Le pourquoi est dans la [décision 0003](decisions/0003-comment-on-travaille.md).

## Quand une issue est prête

Une issue reçoit l'étiquette `prête` quand :

- le besoin tient en une phrase d'utilisateur ;
- les critères d'acceptation sont vérifiables ;
- ce qui est hors du périmètre est écrit ;
- la zone de fichiers et le niveau sont indiqués ;
- elle se fait seule, sans attendre une autre issue, et ne touche pas les mêmes fichiers qu'une
  autre issue prête.

Le formulaire « Fonctionnalité » a un champ pour chacun ; seuls le besoin et les critères y sont
obligatoires, le reste se vérifie avant de poser `prête`.

## Les étiquettes

| Étiquette | Sens |
|---|---|
| `good first issue` | première contribution : petite, guidée, sans prérequis |
| `niveau-2`, `niveau-3` | intermédiaire, confirmé |
| `prête` | remplit la liste ci-dessus |
| `besoin-spec` | le besoin n'est pas encore assez clair pour coder |
| `bloquée` | attend une réponse (de SOS MEDITERRANEE, d'un tech lead) |
| `front`, `back`, `data`, `docs`, `ci` | la zone touchée |
| `bug` | quelque chose ne marche pas |

Elles sont créées par [.github/create-labels.sh](../.github/create-labels.sh).

## Les accès et `main`

- Chaque bénévole reçoit l'accès en écriture au dépôt, pour pousser ses branches : pas de fork.
- `main` est protégée : pull request obligatoire, CI verte obligatoire, une approbation, merge
  en squash. Personne ne pousse directement sur `main`.

## Les issues prises

- Une issue se prend en commentant « Je prends » ; un tech lead l'assigne.
- Une issue assignée sans activité (commit, commentaire, pull request) reçoit un rappel au bout de
  5 jours, et elle est rendue au bout de 7 jours : on retire l'assignation, elle redevient libre.

## La relecture

- Une approbation d'un tech lead suffit pour merger.
- La liste à cocher du modèle de pull request est la définition de « fini ».
- On ne merge que si la CI est verte. Une pull request en brouillon peut avoir des tests rouges :
  c'est normal quand on écrit les tests d'abord.
- Le titre de la pull request suit les commits conventionnels : il devient le message du commit
  sur `main`.

## Les outils

En plus de la CI et de pre-commit, aucun robot n'est installé d'office. Chaque outil (rappel
automatique des issues, vérification des titres de pull request, mise à jour des dépendances…)
arrive par une issue `ci`, que des bénévoles peuvent prendre, comme le polissage de la CI.
