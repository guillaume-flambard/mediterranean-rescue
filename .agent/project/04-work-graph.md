# Graphe de travail

## Historique de la première fondation, remplacée par la tranche REST
F1 P1 DONE inventaire/architecture → AC-F1, EV-F1.
F2 P1 DONE modèles/migrations → AC-F2, EV-F2/F3.
F3 P1 DONE staging/import/publication/administration → AC-F3/F6, EV-F2/F7.
F4 P1 DONE schéma GraphQL/types générés → AC-F3/F4, EV-F4/F5.
F5 P1 DONE frontend Base UI/MapLibre/urql → AC-F5, EV-F4/F6.
F6 P1 DONE Compose/CI/docs → AC-F7, EV-F3/F4/F8 (CI écrite, commandes exécutées localement).
F7 P1 DONE vérification indépendante → EV-F7, contrôles finaux.
F8 P1 DONE défauts découverts : worker MapLibre bundlé, GET Content-Length vide, origine CSRF locale et affichage d’enum → EV-F2/F6.
F9 P1 DONE défauts revue : édition indirecte et formulaires périmés sur contenus publiés → EV-F2/F7.

Produit hors tranche, explicitement en cours : migration réelle/crosswalk, révisions et rapprochements logbook, alias ports/couches qualifiées, identité/hébergement/backup/restauration de production et recette associative.
P2 historique, pagination des preuves résolue dans REST-2 ; restent amélioration du poids cartographique chargé à la demande, filtres spatiaux pilotés par l’interface.

F10 P1 DONE défaut CI Linux : export SDL par stdout et écriture par l’hôte ; utilisateur conteneur non-root conservé. Readiness DB vérifie désormais le compte applicatif en TCP pour éviter le serveur temporaire d’initialisation.

F11 P1 DONE alignement lockfile et pnpm12.10.1 réel (défaut CI d’installation gelée), dépend F10.

Clôture F10/F11 : EV-F11, CI complète verte sur cd69cc4 ; la dernière mise à jour est documentaire.

## Tranche REST et cadrage, 24 octobre 2026
REST-1 P1 DONE spécification ADR0003, preuve : décision utilisateur et contrat écrit.
REST-2 P1 DONE API publique REST/OpenAPI ; R-REST-1/2/3.
REST-3 P1 DONE client généré et interface ; dépend REST-2, R-REST-3/4.
REST-4 P1 DONE tests et CI ; dépend REST-2/3.
REST-5 P1 DONE document de départ, revue indépendante et clôture ; R-DOC-1, dépend REST-4.

Preuves tranche REST : REST-2 EV-R1/R3 ; REST-3 EV-R2/R4 ; REST-4 EV-R2/R3/R6 ; REST-5 EV-R0/R5/R6. Les cinq tâches sont vérifiées ; le produit reste IN_PROGRESS (L1..L5).
