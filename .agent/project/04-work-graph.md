# Graphe fini de la première fondation
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
P2 : plafonnement des preuves imbriquées GraphQL, amélioration du poids cartographique chargé à la demande, filtres spatiaux pilotés par l’interface.

F10 P1 DONE défaut CI Linux : export SDL par stdout et écriture par l’hôte ; utilisateur conteneur non-root conservé. Readiness DB vérifie désormais le compte applicatif en TCP pour éviter le serveur temporaire d’initialisation.

F11 P1 VERIFYING alignement lockfile et pnpm12.10.1 réel (défaut CI d’installation gelée), dépend F10.
