# Mediterranée Rescue — périmètre canonique
24 octobre 2026 — T2, démonstrateur isolé sans données personnelles ni déploiement.

## DISCOVER
Dossier vierge. Annonce fournie par l’utilisateur, source/date non retrouvées. Dépôt public dataforgoodfr/mediterranean-rescue découvert : template Python, commit c3390efe7fe674b645ce32dfc37a340e69e1a042. Carte CartONG préexistante.

## MODEL
Recherche → fiche organisationnelle et message → cadrage humain. POC statique local : JSON synthétique → validation → filtres → carte SVG géographique et liste → détail sourcé. Aucun service distant à l’exécution. Aucune écriture CRM ou envoi.

## SPECIFY
REQ-1 : dossier sourcé séparant faits, hypothèses et inconnues ; contact public vérifié et message pour lundi 26/10 sans envoi. AC-1 : inspection des sources et livrables.
REQ-2 : carte historique synthétique avec filtres date/navire, liste accessible et détail ; AC-2 : test de filtres et essai navigateur.
REQ-3 : import JSON atomique validé (dates, coordonnées, valeurs, sources HTTP/S, IDs uniques), export et remise à zéro ; AC-3 : tests invalides/vides/doublons et navigateur.
REQ-4 : exécution locale hors ligne, documentation et statut honnête ; AC-4 : serveur local, contrôle des ressources et vérification responsive.

## DECOMPOSE
T1 P1 recherche et contact, T2 P1 plan et cadrage (dépend T1), T3 P1 POC (dépend modèle), T4 P1 vérification et preuves (dépend T1,T2,T3). Tous IN_PROGRESS jusqu’à preuve.

## Risques et limites
Statut du recrutement, responsable, année de mars et licence des données opérationnelles inconnus : ne bloquent pas ce démonstrateur ; bloquent engagement ferme et intégration réelle. Les données publiques consultables ne donnent pas automatiquement un droit de réutilisation. Pas d’IA présumée utile. Données intégralement fictives et marquées à chaque vue/export. Pas d’outil de navigation ou de secours.

## Vérification
Tests Node des contrats et filtres ; essai UI navigateur desktop/mobile, sélection, vide, import invalide/valide, reset/export. Inspection finale contre critères. Auth, migrations, concurrence, CI et déploiement N/A (nouveau POC statique local sans persistance). Erreurs d’import visibles, mise à jour atomique et restauration démo. Perf : limite 2000 événements / 2 Mio. Sécurité : texte via textContent, URL HTTP/S seulement ; aucun upload réseau.

## Direction visuelle
Carte principale bleu mer #dceaf0 ; terre #f6f8f7 ; encre #183849 ; accent orange secours #bb471c ; blanc #fff. Typographie système lisible, titre Georgia mesuré. Carte à gauche, journal à droite, filtre horizontal. La priorité est la comparaison carte/liste, sans décoration maritime gratuite.

## Delta utilisateur
Fork demandé explicitement le 24/10/2026 : créé sous guillaume-flambard/mediterranean-rescue, clone dans outputs/mediterranean-rescue. Branche feat/historical-map-poc. Aucune donnée opérationnelle dans les fichiers du dépôt. Construction dans web/ au-dessus du template, sans modifier les dépendances Python héritées. Publication de la branche du fork, sans PR ni message vers Data for Good.

## Défauts découverts par revue indépendante
T5 P1 focus après sélection : restaurer le focus sur le bouton recréé (REQ-2).
T6 P2 focus import : corriger sélecteur CSS vers le label précédant l’input (REQ-3).
T7 P2 import après reset : invalider les lectures en attente au reset (REQ-3).
Implémentés, vérification en cours.

## CLOSE
Statuts des T1 à T7 et preuves finales dans evidence.md ; state.json fait autorité. Les critères d’acceptation sont proportionnés au POC local. Import/export couvert par intégration Node ; boîte native et rendu mobile gardés à la recette manuelle.
