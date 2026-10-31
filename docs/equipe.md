# Pour les tech leads et les PM/PO

Ce que les bénévoles n'ont pas besoin de lire : comment on prépare le travail et comment on le
relit. Le pourquoi est dans la [décision 0003](decisions/0003-comment-on-travaille.md).

## Quand une issue est prête

Une issue reçoit l'étiquette `prête` quand :

- le besoin tient en une phrase d'utilisateur ;
- les critères d'acceptation sont vérifiables ;
- ce qui est hors du périmètre est écrit ;
- la zone de fichiers et le niveau sont indiqués ;
- elle ne dépend d'aucune issue encore ouverte, et ne touche pas les mêmes fichiers qu'une autre
  issue prête.

Le formulaire « Fonctionnalité » a un champ pour chacun ; seuls le besoin et les critères y sont
obligatoires, le reste se vérifie avant de poser `prête`.

## Les étiquettes

| Étiquette | Sens |
|---|---|
| `good first issue` | première contribution : petite, guidée, sans prérequis |
| `niveau-2`, `niveau-3` | intermédiaire, confirmé |
| `prête` | remplit la liste ci-dessus |
| `besoin-spec` | le besoin n'est pas encore assez clair pour coder |
| `bloquée` | attend une réponse ou une autre issue |
| `front`, `back`, `data`, `docs`, `ci` | la zone touchée |
| `bug` | quelque chose ne marche pas |

Elles sont créées par [.github/create-labels.sh](../.github/create-labels.sh).

## La relecture

- Une issue sans nouvelles depuis 7 jours est rendue, après un message à la personne.
- La liste à cocher du modèle de pull request est la définition de « fini ».
- On ne merge que si la CI est verte.
