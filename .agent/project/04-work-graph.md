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

## Tranche donnée D : diagnostic hors ligne des exports Sheets, 24 octobre 2026
Spécification : docs/decisions/0004-data-first.md (dossier de cadrage, documents 04 et 09). Repartie de fa82c99 dans un checkout propre ; l’ébauche locale non publiée n’a pas été reprise telle quelle ni modifiée.
D1 P1 DONE contrat machine lisible contracts/sheets-v1.json et contrôles de structure ; AC-D1.
D2 P1 DONE normalisation candidate dates/effectifs/décimaux/coordonnées/liens ; AC-D2, dépend D1.
D3 P1 DONE provenance exacte, déterminisme, doublons signalés ; AC-D3, dépend D1.
D4 P1 DONE CLI privée bornée, statuts distincts, pas d’écrasement ; AC-D4, dépend D2/D3.
D5 P1 DONE démonstration synthétique étiquetée et rapport lisible ; AC-D5, dépend D4.
D6 P1 DONE revue indépendante et régressions ; dépend D1..D5. Un P1 et sept P2 corrigés avec régressions (EV-D3).
Suite, bloquée par L1 : extrait autorisé, contrat approuvé, crosswalk d’identités, alias de ports, branchement sur le staging.

## Tranche X : correspondance des identités et référentiel des ports, 24 octobre 2026
Spécification : docs/decisions/0005-identity-crosswalk-and-ports.md. Branche feat/ports-and-crosswalk, empilée sur feat/sheets-diagnostic.
X0 P1 DONE conventions de langue (AGENTS.md) et rapport du diagnostic en anglais par défaut avec traduction française.
X1 P1 DONE snapshot persistant et staging privé ; AC-X1.
X2 P1 DONE identités et liens approuvés, propositions calculées ; AC-X2, AC-X3.
X3 P1 DONE référentiel des ports et lectures de libellés (ports, navire, pas un port) ; AC-X4.
X4 P1 DONE revue indépendante, régressions, essai privé sur l'export réel ; AC-X5.
Suite : interface de revue (application React), brouillons d'événements depuis les identités, revue humaine des 29 libellés non résolus et des 3 ports ambigus.

## Tranche B : brouillons d'événements depuis les identités, 24 octobre 2026
Spécification : docs/decisions/0006-event-drafts-from-identities.md. Branche feat/event-drafts, empilée sur feat/ports-and-crosswalk, développée dans un worktree séparé parce qu'une autre session écrivait le design system dans le checkout principal.
B1 P1 DONE traçabilité brouillon sur l'identité (migration 0003, contrainte tout ou rien).
B2 P1 DONE plan et création des brouillons, lignes écartées toujours listées ; AC-D1 à AC-D4.
B3 P1 DONE revue indépendante, régressions, essai privé ; AC-D5.
Suite : révisions revues d'un brouillon (`revision_needed`), preuves documentaires, voyages et navires, écrans de revue dans l'application React.

## Tranche R : révisions revues des brouillons, 24 octobre 2026
Spécification : docs/decisions/0007-reviewed-draft-revisions.md. Branche feat/draft-revisions, empilée sur feat/event-drafts, développée dans un worktree séparé.
R1 P1 DONE trace EventRevision et état de référence `drafted_values` (migration 0004).
R2 P1 DONE proposition, conflits, application et refus ; AC-R1 à AC-R4.
R3 P1 DONE revue indépendante, régressions, essai privé ; AC-R5.
Suite : application React avec écrans de revue (identités, ports, brouillons, révisions), puis preuves documentaires, voyages et navires.

## Tranche UI0 : fondations du frontend, 24 octobre 2026
Spécification : DESIGN.md, docs/design/ (commité tel quel en db3cd3b) et docs/decisions/0008-frontend-foundations.md. Branche feat/ui-foundations, empilée sur feat/draft-revisions, développée dans un worktree séparé.
U0-1 P1 DONE outillage React Compiler, ESLint hooks, Vite 8.3.5, étape lint en CI.
U0-2 P1 DONE i18n anglais par défaut, traduction française typée, écran public passé aux catalogues.
U0-3 P1 DONE tokens, police auto-hébergée, seize composants P1, page interne de catalogue.
U0-4 P1 DONE annulation des requêtes hors query (useAbortableRequest), revue indépendante et corrections.
Reste UI0 : SearchCombobox, NavigationDrawer, DataTable, FilterBar, FileInput ; puis UI1 (API privées de revue et écrans).
