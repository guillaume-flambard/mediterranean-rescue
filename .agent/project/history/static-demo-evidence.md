# Preuves et clôture du périmètre

24 octobre 2026. État : READY_FOR_MANUAL_ACCEPTANCE.

## Critères

| Critère | Preuve | Résultat |
| --- | --- | --- |
| AC-1 recherche, contact vérifié, message lundi non envoyé | outputs/recherche-et-plan.md, fiche-contact.md, message-lundi-26-octobre.txt et .eml ; sources primaires liées | PASS inspection ; inconnues conservées |
| AC-2 filtres, liste, détails et carte | EV-2 tests, EV-3 navigateur | PASS |
| AC-3 validation, import atomique, export et reset | EV-1 et EV-2 | PASS automatisé |
| AC-4 exécution locale sans dépendance réseau et documentation | EV-3 à EV-5, README.md, web/DATA.md, web/PROVENANCE.md | PASS dans la portée documentée |

Les fichiers de contact/recherche sont des livrables privés adjacents au clone dans outputs/, pas des fichiers publiés sur le fork.

## Vérifications

EV-1 : cycle rouge initial, `node --test web/model.test.cjs` échoue car model.js n’existe pas ; après implémentation, 6 tests passent. Validation de date réelle (dont année bissextile), coordonnées, types, effectifs, doublons, URLs et caractère fictif.

EV-2 : `node --test web/model.test.cjs web/app.test.cjs` : 10 tests, 10 PASS, 0 FAIL. Les tests d’intégration exécutent les vrais handlers avec un DOM minimal : focus, sélection retirée au filtre, période inversée/vide, import invalide conservant le jeu, dataset vide, restauration, import valide, limite fichier, contenu texte inerte, téléchargement initié. Test de régression pour une lecture en attente invalidée par reset.

EV-3 : serveur Python lié à 127.0.0.1:8765, fichiers web servis. Essai dans le navigateur Codex : 6 événements/308 personnes fictives ; sélection DEMO-006 donnant date/navire/position/note/source ; focus maintenu sur l’événement après correction ; Navire B donne 2 événements/89 personnes fictives ; début en 2025 donne zéro et désactive export ; zoom et Vue complète changent l’état des commandes. Capture outputs/apercu-carte.png. La sélection de fichier via la boîte native n’a pas pu être pilotée par l’outil disponible ; le parcours import/export est vérifié par les handlers automatisés. Le fichier exporté réel et le rendu sur téléphone restent des vérifications manuelles conseillées, sans prétendre les avoir exécutées.

EV-4 : `node --check web/app.js` PASS ; `git diff --check` PASS. `uvx pre-commit run --all-files` : ruff, check-merge-conflict et mixed-line-ending PASS. Les hooks ont été initialisés après indexation des nouveaux fichiers. Le test Tox hérité py310/Poetry ne correspond pas au projet uv Python >=3.12 ; non exécuté et hors de cette contribution web isolée. Aucun changement à la base Python.

EV-5 : inspection des ressources : HTML, CSS, JavaScript et fond Natural Earth locaux. Aucun fetch, CDN, analytics ou stockage applicatif. Les liens externes sont explicites et requièrent un clic. Le JSON importé est réduit aux champs attendus ; rendu texte via textContent, URLs HTTP/S sans identifiants. CSS mobile à 760 px, contrôles flexibles et liste alternative inspectés ; aucune validation mobile sur appareil prétendue.

EV-6 : revue indépendante en lecture seule. Trois constats initiaux corrigés : focus de sélection, focus import, course import/reset. Deuxième revue exécute les 10 tests et ne trouve aucun P0/P1 résiduel dans la portée. Elle confirme les limites du DOM minimal et la nécessité d’une recette visuelle humaine.

EV-7 : le message a été contrôlé par humanizer/lint.py : aucun motif signalé. Fiche organisationnelle vCard créée sans personne ni téléphone inventé. Aucun message envoyé, aucun engagement horaire ferme, aucune inscription effectuée.

## Graphe fini et statut

T1 P1 recherche/contact DONE (AC-1, EV-7, sources). T2 P1 plan/cadrage DONE (AC-1, livrable privé). T3 P1 POC DONE (AC-2/3, EV-1/2/3). T4 P1 vérification DONE (EV-1 à EV-7). T5 P1 focus DONE (EV-2/3/6). T6 P2 focus import DONE (EV-5/6). T7 P2 course import DONE (EV-2/6).

P0 ouverts : 0. P1 ouverts : 0. Critères échoués : 0. Critères sans preuve dans la portée : 0. Risques élevés/critiques du POC : 0.

## Limites et suites hors périmètre

Le recrutement et la personne responsable restent inconnus ; le lien entre le dépôt et l’annonce est une hypothèse appuyée par le nom, pas une confirmation officielle. Données réelles, licence, périmètre métier, précision et année de mars sont à obtenir avant une intégration réelle ou un engagement. La carte synthétique sert à discuter de l’interface, pas à revendiquer une solution adoptée. Limites géographiques et performance explicites dans README/DATA.

P2 différés : adaptateur autorisé de données réelles après cadrage ; choix de cartothèque pour une résolution côtière ; recette sur appareils mobiles ; CI dédié au POC si l’équipe le conserve. Aucune intégration, persistance, migration, authentification ou mise en production dans cette tranche.

## Acceptation manuelle

1. Ouvrir la carte locale ou web/index.html, filtrer et consulter une fiche.
2. Essayer l’import du JSON fourni, un fichier invalide, l’export et la restauration.
3. Lire le message et ajuster sa signature/disponibilité avant envoi manuel lundi 26 octobre.

L’acceptation humaine n’est pas enregistrée. Statut final contrôlé par l’agent : READY_FOR_MANUAL_ACCEPTANCE.
