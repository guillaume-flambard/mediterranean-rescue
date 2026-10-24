# Preuves de la fondation

24 octobre 2026. Cette clôture porte sur la première fondation exécutable, pas sur la plateforme entière ni son adoption par SOS/DfG.

EV-F1 : architecture, décision GraphQL et catalogue écrits dans docs/. Recherche indépendante des 3 adaptateurs CartONG, fichiers géographiques et journal de bord. Licence inconnue conservée comme inconnue, aucune donnée réelle ou code CartONG recopié. Version Base UI 1.9 observée dans le projet récent Memo Orbit et documentation officielle consultée.

EV-F2 : `docker compose run --rm api uv run --no-sync python backend/manage.py test catalog.tests --noinput` : 18 tests PASS sur PostgreSQL 17.11 / PostGIS 3.6.4 réels. Couverture : brouillons/sources sans droits invisibles, permission/revue/motif, audit/retrait, contrainte SQL de publication, import atomique/idempotent, champs inconnus null, dates/coordonnées/URL invalides, refus d’écrasement, filtres communs liste/carte et bbox, contrat public limité, pagination/alias/mutations, budget de 3 requêtes SQL pour 5 événements et relations, séparation training/production, CSRF et taille HTTP, champs relationnels gelés, licence blanche masquée, GET Content-Length vide/origine proxy, formulaires périmés et déplacement de preuve protégés. Dernier test inverse puis réapplique la migration catalog uniquement dans la base test_ dédiée, et vérifie la recréation des tables. Base de test détruite par le runner.

EV-F3 : migration 0001 appliquée avec succès à la base locale dédiée, puis `makemigrations --check --dry-run` : No changes detected. `check --deploy --fail-level WARNING` avec DJANGO_ENV=production et domaine rescue.invalid : no issues, sans déploiement. Les secrets locaux sont générés hors Git, non affichés. Aucune migration d’une base associative externe.

EV-F4 : export Django de contracts/schema.graphql, puis `pnpm codegen` PASS ; `pnpm test` : 2 tests frontend PASS ; `pnpm build` : TypeScript strict et build Vite PASS. Base UI 1.9, React19.3.1, MapLibre6.15, urql5.0.4 verrouillés. MapLibre est chargé à la demande ; son worker est émis explicitement en ressource locale. Avertissement de taille du chunk carte restant documenté, entrée principale environ393Ko avant gzip, carte environ1056Ko avant gzip.

EV-F5 : `python3 scripts/check_contract_negative.py` PASS : une opération temporaire visant fieldThatMustNotExist échoue à la génération pour cette raison ; fichier temporaire retiré. Le frontend consomme des TypedDocumentNode générés, pas des DTO Event recopiés. Les scalaires Date et UUID sont mappés explicitement ; strictScalars et TS strict activés. Le workflow CI réexporte, régénère et refuse la dérive des fichiers versionnés.

EV-F6 : essai navigateur à http://127.0.0.1:5173/, API réelle locale. État loading puis base vide correctement affiché, fond Natural Earth visible et zoom, ouverture du Select Base UI et choix Sauvetages avec libellé humain, réponse GraphQL valide, dates inversées signalées et reset testé. Vue étroite 430px inspectée, carte et liste empilées. Défauts worker Vite et GET sans Content-Length trouvés à l’exécution et corrigés ; régression HTTP ajoutée. Capture outputs/apercu-plateforme.png adjacente au dépôt. Les fiches d’événements positifs sont couvertes par contrats/build et backend tests ; recette visuelle sur données métier et tous appareils non prétendue réalisée.

EV-F7 : revue indépendante lecture seule. Première suite 12 puis15 tests PostGIS PASS. La revue a identifié chemins admin de mutation indirecte et instances périmées ; corrections appliquées avec tests. Dernière relecture ne trouve aucun P0/P1 résiduel dans les gardes examinées. Dernier passage de 18 tests exécuté par l’intégrateur, sans l’attribuer au relecteur.

EV-F8 : Ruff check et format backend/scripts PASS ; contrôles de hooks dépôt et diff final enregistrés après indexation. Images Compose construites, locks Python/pnpm fournis. Le workflow CI est ajouté sur la branche ; ne pas confondre ces exécutions locales avec un run GitHub Actions distant, qui doit être consulté séparément.

## Couverture d’acceptation
AC-F1 → EV-F1 ; AC-F2 → EV-F2/F3 ; AC-F3 → EV-F2/F7 ; AC-F4 → EV-F4/F5 ; AC-F5 → EV-F4/F6 ; AC-F6 → EV-F2 ; AC-F7 → EV-F3/F4/F8. Critères vérifiés 7/7, échoués0, P0/P1 ouverts0 dans cette tranche.

## Limites concrètes
Pas d’import réel des Sheets sans droits/dictionnaire/crosswalk validés. Le normaliseur canonique v1 n’est pas un connecteur Sheets caché. Pas de mutation publique, abonnement temps réel, tâche réseau autonome ou hébergement lancé. Identité de production, restauration hors site, recette associative, couches autoritatives, révisions d’effectifs et liens logbook sont la roadmap suivante. Les relations imbriquées de preuves ne sont pas paginées ; suivi P2 avant gros volumes. La carte plafonne explicitement ses points à2000 et la liste à100 par requête (UI25).

EV-F9 : premier run GitHub Actions 40089304145 : tests backend, migrations et configuration prod PASS ; export SDL échoue sur permissions du bind mount Linux. Correction par export stdout puis redirection hôte, sans exécuter en root. Nouvelle CI en attente.

EV-F10 : second run 40089444379 : export SDL corrigé PASS ; installation gelée frontend révèle le document de pin pnpm manquant dans le lockfile (CLI local réel 11.25 malgré le pin12). Régénération du lockfile avec le binaire pnpm12.10.1 explicite, sans désactiver frozen-lockfile ni les politiques de supply chain. Vérification locale/CI finale en cours.

EV-F11 : GitHub Actions https://github.com/guillaume-flambard/mediterranean-rescue/actions/runs/40089645162 sur cd69cc4 : SUCCESS. Image backend et DB construite, 18 tests backend, migration contract, contrôle configuration production, export SDL portable, installation pnpm12 gelée, génération TS, refus de dérive, test négatif et tests/build frontend tous PASS. Les échecs précédents sont résolus par corrections, sans contourner les contrôles. F10 et F11 DONE. Fondation READY_FOR_MANUAL_ACCEPTANCE ; produit IN_PROGRESS.
