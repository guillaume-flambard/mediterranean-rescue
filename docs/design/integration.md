# Portée et preuves : design system et parcours

Demande de Guillaume du24 octobre2026 : préparer le design system Base UI dans le dépôt actif, puis un plan très concret de parcours, en recherchant des références UX pour une expérience intuitive et interactive.

## Portée

Documents, références visuelles et tokens uniquement. Aucun composant React, écran, contrat API ou modèle métier modifié. Le travail de l’autre agent sur la donnée reste autonome. Les composants et routes sont des cibles, pas des fonctionnalités présentées comme disponibles. Le CSS de référence reste sans import frontend ; aucune police ou dépendance n’est ajoutée au produit.

Le design est décrit dans DESIGN.md et docs/design/. L’état documentaire local est dans status.json ; il ne remplace pas l’état global du chantier donnée dans .agent/project/.

## Critères

- DS-1 : fondations et états cohérents dans JSON/CSS ; origine observée/proposée distincte.
- DS-2 :26 contrats de composants, primitives Base UI installées vérifiées, comportements et limites d’accessibilité décrits.
- UX-1 : parcours privés et publics explicites, routes/actions/erreurs/reprises et dépendances serveur identifiées.
- UX-2 : références primaires et objectifs d’essais mesurables, sans fausse validation d’intuitivité.
- DOC-1 : liens autonomes, planches lisibles, priorité donnée et Base UI conservées, absence de modification applicative.

## Historique et revue

Le premier relevé de marque a été intégré dans ce checkout à la demande de Guillaume. Pendant cet ajout, l’agent donnée a committé son propre chantier e0d1d5e ; aucune restauration ou modification de son travail n’a été effectuée.

La présente extension a été relue indépendamment en lecture seule. Un défaut de génération CSS (breakpoints sérialisés en dictionnaire) a été identifié puis corrigé : les seuils restent dans le JSON, et les media queries futures utilisent des conditions statiques. Les autres clarifications intégrées concernent la route temporaire de diagnostic avant snapshot, le bouton distinct Créer l’identité et l’exclusion des positions inconnues par une bbox.

Les deux planches sont des références statiques sur contenu synthétique. Elles ont été inspectées visuellement ; elles ne prouvent pas les interactions Base UI ni l’accessibilité d’une application.

## Vérifications

- DS-1 PASS : JSON valide ; palette, rôles, échelles et références CSS concordants ; aucune variable indéfinie ; réduction du mouvement explicitée. Onze associations de texte prévues dépassent4,5:1 ; quatre associations de contrôle/focus prévues dépassent3:1. Les ratios portent sur ces associations, pas sur un audit complet de tous les écrans.
- DS-2 PASS :26 contrats écrits ;18 exports publics Base UI1.9.0 vérifiés dans le package installé. Les composants projet restent à implémenter.
- UX-1 PASS :12 écrans/routes cibles ; cinq parcours, cas d’échec et dépendances des APIs privées documentés. Revue indépendante finale sans blocage restant identifié.
- UX-2 PASS : références primaires consultées et objectifs d’essais avec bénévoles écrits. Aucune séance n’est déclarée réalisée.
- DOC-1 PASS : liens des sept documents Markdown de référence vérifiés ; deux planches inspectées après correction des états de boutons et du contenu. Aucun fichier applicatif suivi ni index modifié ; ajouts sous DESIGN.md et docs/design uniquement.

Aucune suite backend/DB n’est requise pour cette modification documentaire. Les preuves applicatives et les séances d’utilisabilité restent à produire lors des lots UI0 àUI5.

Statut de cette livraison documentaire : READY_FOR_MANUAL_ACCEPTANCE, critères5/5, P0/P1 restants0 dans ce périmètre. L’application et ses parcours ne sont pas implémentés par cette tâche. Les fichiers restent locaux, sans commit/push sur la branche du chantier donnée. La prochaine tâche de code est UI0, puis UI1 selon les dépendances décrites.
