# READY_FOR_MANUAL_ACCEPTANCE : REST et document de départ

Résultat : document complet docs/PROJECT.md et fork initialisé, backend REST/OpenAPI et frontend Base UI raccordés avec types générés. Remplacement de GraphQL, conservation du domaine, des données locales et de l’historique.

P0 restants 0 ; P1 restants 0 ; critères vérifiés 5/5 ; critères en échec/en attente 0 ; risques critiques/élevés ouverts 0 dans la portée de cette tranche. Tests 19 backend + 2 frontend PASS, contrat/build/CI et revue indépendante PASS (EV-R0..R6).

Limites et travaux différés : poids du module carte, filtres spatiaux/URL côté UI, recette positive sur données métier autorisées, lots L1..L5. Aucune donnée réelle importée et aucun lancement public prétendu. Le produit entier reste IN_PROGRESS.

Recette humaine : lire le document de départ, lancer via README, consulter carte/liste et filtres ; voir 08-manual-acceptance.md. Statut humain non acquis.

# READY_FOR_MANUAL_ACCEPTANCE : diagnostic hors ligne des exports Sheets

Résultat : contrat `contracts/sheets-v1.json`, module stdlib `backend/catalog/sheets.py`, CLI `scripts/diagnose_sheets.py`, fixtures et exemple synthétiques, ADR 0004. D1..D6 DONE, AC-D1..D5 vérifiés (EV-D0..D4). P0/P1 ouverts 0. CI GitHub de la PR à consulter avant fusion.

Hors tranche : aucune donnée réelle, aucun import ni staging, aucun crosswalk. La recette humaine (08-manual-acceptance.md) n’est pas acquise.
