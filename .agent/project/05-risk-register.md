# Risques de la tranche
R1 fuite brouillons : MITIGATED, queryset public canonique, types explicites, tests public/private et modes training/production EV-F2.
R2 publication/permission/édition indirecte : MITIGATED, permissions, verrous, contrôle de version des formulaires, audit et gel relations publiées EV-F2/F7.
R3 dérive contrats : MITIGATED, export/codegen/typecheck et test négatif EV-F4/F5.
R4 droits inconnus sources réelles : MITIGATED pour la tranche par absence de copie et publication réelle ; reste condition préalable d’une future migration.
R5 erreurs position/date/comptage : MITIGATED, validation serveur, nulls et tests PostGIS EV-F2.
R6 complexité : monolithe et aucun broker/file externe, documentation des étapes réelles.
R7 ARM PostGIS : MITIGATED, image officielle amd64 sous émulation, tests réels PG17.11/PostGIS3.6.4 EV-F2.
R8 fausse complétion : état de fondation distinct du produit toujours en cours.
Risques élevés/critiques ouverts dans la portée fondation locale : 0. Aucune mise en production annoncée.

Actualisation REST : R1/R2/R5 revérifiés EV-R1/R3 ; R3 par OpenAPI/TS déterministes et négatif EV-R2/R5/R6. Revue indépendante EV-R5 sans P0/P1 restant. Limites P2 : poids cartographique et emprise/filtres partageables côté interface. Pagination des preuves résolue par endpoint borné. Les inconnues de droits et exploitation bloquent L1/L5, pas la tranche locale close.
