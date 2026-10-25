# ADR 0016 : démonstration publique sur rescue.memolabs.dev et publication du tableur

Statut : accepté le 25 octobre 2026, décision de Guillaume (« toutes les données sont publiques, pourquoi les cacher ? Pour la démo il faudra bien le site public »).

## Contexte
Le site public ne montre que des événements publiés par une personne nommée, avec un motif, depuis une source dont l'accord de publication est enregistré (ADR 0006, 0013). Rien n'était publié : la démonstration aurait montré une carte vide. Le projet devient public (dépôt `memolabs-dev/mediterranean-rescue`) et tourne sur `rescue.memolabs.dev`.

## Décision
- **Le tableur de la carte CartONG se publie en une décision.** Ses lignes sont déjà visibles par tous sur la carte de SOS MEDITERRANEE. `manage.py publish_source --source <clé> --actor <personne> --reason "<motif>" [--apply]` relie chaque nouvelle ligne du dernier export à une nouvelle identité, prépare les brouillons et les publie, sous le nom et le motif donnés, dans une transaction. Chaque décision reste enregistrée comme si elle avait été prise à l'écran (lien, brouillon, audit de publication) et apparaît dans l'Historique.
- **Ce que la commande ne fait pas.** Les lignes en erreur, les doublons, les correspondances possibles et les brouillons refusés par les contrôles (chiffres incohérents, position 0,0) restent pour l'espace équipe. Sans `--apply`, elle parcourt tout puis annule : les nombres affichés sont exacts. Elle refuse une source sans accord enregistré, une personne sans les trois permissions (vérifier, préparer, publier) et le journal de bord.
- **Le journal de bord reste vérifié ligne à ligne.** Ses lignes sont notre lecture d'un texte, et 35 sur 69 portent un doute ; elles sont publiées une par une dans l'espace équipe, après vérification.
- **L'accord de la source** est coché par le propriétaire du projet dans l'administration, avec la note : données déjà publiées par SOS MEDITERRANEE sur sa carte, reprises avec leur source pour une démonstration indépendante. Ce n'est pas un accord écrit de l'association ; il reste à obtenir avant tout usage au-delà de la démonstration (ADR 0014).
- **Déploiement.** Une image (`Dockerfile` à la racine) sert l'API et le site construit (WhiteNoise), avec une politique de sécurité du contenu stricte ; la même image fait tourner les deux lecteurs planifiés. Pile de référence : `deploy/compose.yaml`. Sur le lab Memo Labs : `stacks/rescue` du dépôt d'infrastructure, image GHCR construite par la CI à chaque fusion sur `main`.

## Conséquences
- La démonstration montre les 10 ans d'opérations du tableur, avec leur source, et les lignes du journal au fur et à mesure de leur vérification.
- Le site affiche qu'il est un projet indépendant, non affilié à SOS MEDITERRANEE.
- Retirer reste possible à tout moment depuis l'espace équipe, événement par événement, avec un motif.
