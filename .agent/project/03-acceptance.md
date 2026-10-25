# Acceptation
AC-F1 (F1) : architecture et dictionnaire distinguent observé/inconnu, données et droits. Inspection.
AC-F2 (F2,F7) : migrer une base PostGIS vierge, aucune migration manquante, test spatial sur DB réelle.
AC-F3 (F3,F6) : brouillon/source sans droits invisibles ; publication refusée sans permission/licence ; audit et retrait contrôlés ; pagination/filtres invalides/depth/aliases testés.
AC-F4 (F4) : schéma exporté déterministe, génération des requêtes TS et typecheck/build passent ; une opération invalide est rejetée par génération.
AC-F5 (F5) : UI charge le backend et distingue vide/erreur/entraînement ; Base UI effectivement utilisé ; essai navigateur.
AC-F6 (F6) : import identique idempotent, erreur ne publie rien, checksum/provenance conservés, inconnus non transformés en zéro.
AC-F7 (F7) : commandes documentées et CI cohérente, contrôle sécurité Django production, pas de secret/payload réel dans Git.
Preuves en attente dans 07-evidence.md.

## Critères de la tranche REST et cadrage
AC-R1 = R-REST-1 : brouillon/retrait/révocation/train exclus et champs internes absents ; tests HTTP.
AC-R2 = R-REST-2 : filtres identiques, 400/404/405, pagination et limite carte ; tests HTTP/budget SQL.
AC-R3 = R-REST-3 : OpenAPI sans avertissement, régénération déterministe et compilation négative ; CI et commandes locales.
AC-R4 = R-REST-4 : carte/liste/détail avec hooks REST, test/build et parcours navigateur.
AC-R5 = R-DOC-1 : document de départ, cinq lots dépendants, critères/risques et README exact ; inspection des liens et revue.
Preuves courantes : section EV-R de 07-evidence.md (en cours).

## Critères de la tranche donnée D (diagnostic hors ligne)
AC-D1 : en-tête dupliqué/inconnu, colonne obligatoire absente, cellules en trop ou manquantes, colonne anonyme vide/non vide, guillemets mal formés ; dérive signalée, cellules brutes conservées, aucun décalage.
AC-D2 : date impossible et bissextile, format de l’autre onglet, inconnu/zéro, négatif/fractionnaire, virgule décimale, coordonnées et hémisphères, bornes exactes avant conversion, minutes à 60, liens dangereux ou avec identifiants, listes label/url désalignées.
AC-D3 : BOM, cellule multi-ligne, doublon, même fichier rejoué, ligne déplacée ; empreinte et ligne physique exactes, déterminisme, ni fusion ni identité.
AC-D4 : plus de 5 Mio, plus de 10 000 enregistrements, UTF-8 invalide, CSV interrompu, dossier existant, erreur d’écriture, sentinelles absentes de stdout/stderr/rapport, modes 0700/0600, .gitignore local.
AC-D5 : trois fixtures fictives étiquetées, rapport lisible, aucune conclusion sur le vrai jeu de données.
Régressions : suite Django/PostGIS existante, migrations, check --deploy, OpenAPI et types inchangés, négatif TS, tests et build frontend.

## Critères de la tranche X
AC-X1 à AC-X5 : voir docs/decisions/0005-identity-crosswalk-and-ports.md.
