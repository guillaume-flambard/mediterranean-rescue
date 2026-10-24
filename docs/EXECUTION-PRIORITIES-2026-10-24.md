# Cadre d'execution — 24 octobre 2026

Decision de Guillaume : **aucun gel, aucune suppression et aucun retour en arriere**. Terminer integralement le chantier deja engage sur `feat/import-ports-ui`, puis recadrer les futurs travaux backend autour des besoins verifies de SOS MEDITERRANEE et Data for Good.

## Maintenant — finir le chantier engage

Conserver tous les travaux deja entames : carte, frise, journal, interface publique, espace equipe, imports, revue, ports, roles, preparation et publication. Achever les flux et leur recette plutot que changer de direction.

Verifier le parcours local sur donnees de test : import > anomalies > identites > brouillons > decisions de publication autorisees > affichage public > retrait. Tester aussi les refus de permission, doublons, erreurs, accessibilite mobile, EN/FR, build, PostGIS et contrats OpenAPI. Ne pas publier de donnees reelles sans droits.

Ne pas ouvrir de PR vers Data for Good, ni deployer officiellement sans decision de Guillaume. Les exigences du lot actif restent applicables.

## Ensuite — prochain lot backend

Avant toute nouvelle fonctionnalite, documenter : (1) l'utilisateur et son probleme, (2) la preuve du besoin, (3) ce que CartONG fournit deja, (4) la solution minimale, (5) les droits sur les donnees, (6) le critere de recette.

La carte CartONG existante couvre deja operations, cartes, filtres, chronologie, graphiques et fiches. Le depot officiel Data for Good est encore un squelette Python. L'annonce publique demande de construire une stack cartographique et d'accueillir des benevoles; elle ne precise ni refonte ni nouveau besoin fonctionnel.

Priorites candidates : qualite et provenance des donnees, rapprochement des identites entre exports, corrections revues, droits de publication, tests et onboarding des benevoles. **Ce sont des choix techniques du fork, pas des besoins approuves de SOS.**

Maintenir trois scenarios ouverts : completer CartONG; le moderniser si mission confirmee; construire un produit distinct si usage reellement nouveau. Aucun remplacement automatique.

## Inconnues a qualifier

Pourquoi CartONG ne suffit-il pas ? Qui actualise et valide les Sheets ? Quel produit, pour quel public, doit etre livre ? Qui autorise la reutilisation et l'exploitation ?

**Boussole : finir ce qui est commence. Ensuite, une nouvelle feature backend doit resoudre une lacune demontree et non un probleme suppose.**
