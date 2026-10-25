# ADR 0012 : relecture du tableur toutes les 5 minutes, et séparation public / équipe

Statut : décidé par Guillaume le 24 octobre 2026 (« on va pour les 5 minutes » ; « je veux ce que l'utilisateur voit et ce que l'admin voit, et que ce soit clair »). Remplace la partie « aperçu sur l'écran principal » de l'ADR 0011.

## Séparation public / équipe
- La page principale (`/`) ne montre que les événements publiés, même à une personne connectée. Un lien « Espace équipe » mène au travail de l'équipe.
- L'Espace équipe gagne une première section, « Dernières données » (`/workspace/data`) : la même lecture (fil, carte, fiches) sur les dernières données reçues, avec leur état, et la fraîcheur du tableur.
- Les écrans de l'équipe sont écrits pour des personnes non techniques, comme les pages publiques (PRODUCT.md).

## Relecture automatique
- Commande `sync_sheets` (une passe, ou `--every 300`), configurée par un fichier local (`SHEETS_SYNC_CONFIG`, hors Git) qui donne la source et l'adresse d'export CSV de chaque onglet.
- Chaque passe télécharge l'export public (https, `docs.google.com` puis redirection vers `*.googleusercontent.com` seulement, taille limitée par le contrat, délai 30 s). Octets identiques à la dernière copie : « inchangé ». Sinon `stage_snapshot` rediagnostique et garde la copie en privé ; une copie non enregistrable est « refusée » avec son motif ; une erreur réseau est « échec ». Rien n'est rattaché, rédigé ni publié automatiquement.
- Chaque passe laisse une trace `SheetSync` (onglet, état, copie, empreinte, compteurs, message sans valeur source). `GET /api/private/v1/sync/` donne à l'équipe l'heure de la dernière lecture et ce que la dernière mise à jour apporte : à regarder, à corriger dans le tableur, inchangés.
- Les enregistrements automatiques sont signés par un compte `sheets-sync` qui ne peut pas se connecter.

## Pourquoi pas mieux tout de suite
Recherche du 24 octobre 2026 : les notifications Drive ne disent pas ce qui a changé, expirent au plus après un jour et sans garantie de livraison ; les déclencheurs Apps Script exigent un accès d'édition au tableur. La relecture régulière est simple et fiable ; un déclencheur Apps Script ou une notification pourra s'y ajouter plus tard, sans la remplacer. Le vrai verrou reste l'absence d'identifiant stable par opération dans le tableur : à proposer à SOS MEDITERRANEE (colonne ID remplie par script).

## Robustesse (revue indépendante du 24 octobre 2026)
- « Inchangé » compare l'empreinte à la lecture précédente, pas à la dernière copie créée : un tableur revenu à un ancien contenu est un seul changement, puis « inchangé » ; l'état affiché décrit ce que le tableur contient maintenant.
- Un téléchargement plus court que la taille annoncée, trop gros ou plus long que 90 s est refusé.
- Une erreur inattendue sur un onglet est notée « échec » sans arrêter les autres ni la boucle ; une coupure de la base est absorbée entre deux passes.
- Une seule lecture à la fois (verrou PostgreSQL), configuration vérifiée au démarrage, compte `sheets-sync` refusé s'il peut se connecter.

## Limites
Exécution locale pour l'instant (boucle lancée à la main) ; l'hébergement et l'ordonnanceur de production restent à décider. Les traces `SheetSync` n'ont pas encore de durée de conservation (environ 860 par jour pour trois onglets). Le domaine `*.googleusercontent.com` accepté pour les redirections couvre aussi d'autres contenus Google : la configuration doit rester sous la main de l'équipe technique.
