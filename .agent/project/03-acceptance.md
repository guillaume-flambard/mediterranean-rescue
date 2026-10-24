# Acceptation
AC-F1 (F1) : architecture et dictionnaire distinguent observé/inconnu, données et droits. Inspection.
AC-F2 (F2,F7) : migrer une base PostGIS vierge, aucune migration manquante, test spatial sur DB réelle.
AC-F3 (F3,F6) : brouillon/source sans droits invisibles ; publication refusée sans permission/licence ; audit et retrait contrôlés ; pagination/filtres invalides/depth/aliases testés.
AC-F4 (F4) : schéma exporté déterministe, génération des requêtes TS et typecheck/build passent ; une opération invalide est rejetée par génération.
AC-F5 (F5) : UI charge le backend et distingue vide/erreur/entraînement ; Base UI effectivement utilisé ; essai navigateur.
AC-F6 (F6) : import identique idempotent, erreur ne publie rien, checksum/provenance conservés, inconnus non transformés en zéro.
AC-F7 (F7) : commandes documentées et CI cohérente, contrôle sécurité Django production, pas de secret/payload réel dans Git.
Preuves en attente dans 07-evidence.md.
