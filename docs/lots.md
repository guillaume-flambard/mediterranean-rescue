# Lots

Le travail découpé pour les bénévoles : un but, de quoi il dépend,
s'il est délégable, la zone de fichiers, et ce qui dit qu'il est fini. On prend un lot « prêt »,
on l'annonce sur le canal, une branche, une petite pull request.

Statuts : à définir, prêt, en cours, livré (ou bloqué, abandonné).

| ID | Lot | Statut | Dépend de | Délégable | Zone |
|---|---|---|---|---|---|
| L01 | Socle minimal : Vue, Django SQLite, carte MapLibre, tests ([0002](decisions/0002-socle-minimal-officiel.md)) | livré | aucun | non | tout |
| L03 | Fiche complète d'une opération | prêt | L01 | oui | `frontend/src/components/`, `backend/operations/` |
| L04 | Chiffres clés | prêt | L01 | oui | `frontend/src/components/`, `backend/operations/views.py` |
| L05 | Filtre par dates et histogramme par mois | prêt | L01 | oui | `frontend/src/components/`, `backend/operations/views.py` |
| L06 | Légende complète et couches (ports, régions SAR, eaux territoriales) | prêt | L01 | oui | `frontend/src/views/MapView.vue`, `frontend/public/` |
| L07 | Fonds de carte libres (PMTiles), dont satellite ou perte assumée | à définir | L01 | oui | `frontend/public/`, `MapView.vue` |
| L08 | Allemand et italien | prêt | L01 | oui | `frontend/src/` (vue-i18n à ajouter) |
| L09 | Entête : glossaire, journal de bord, don ; contributeurs | prêt | L01 | oui | `frontend/src/views/` |
| L10 | Visite guidée | à définir | L03 à L06 | partiel | `frontend/src/components/` |
| L11 | Mobile : menu, chiffres compacts | prêt | L04 | oui | `frontend/src/views/` |
| L13 | Image de production et CI (CI faite, reste l'image) | prêt | L01 | oui | `.github/workflows/`, déploiement |

## Fini, pour chaque lot

- Les tests du lot passent (`pnpm test`, et `pnpm test:e2e` si le lot touche un parcours).
- Les vérifications de `TECHNICAL.md` sont vertes (backend et frontend).
- Couleurs et espacements issus des jetons ; textes en anglais et en français une fois le lot L08 livré.
- Aucune ligne de code CartONG ; la colonne « Ici » de `docs/parite-cartong.md` est mise à jour.

Le détail de chaque lot prêt est dans son issue.
