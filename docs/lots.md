# Lots

Le travail découpé en grands morceaux : un but, s'il est délégable, la zone de fichiers, et ce
qui dit qu'il est fini. Chaque lot se découpe ensuite en issues, et c'est une issue qu'on prend,
jamais un lot entier.

Statuts : à définir, prêt, en cours, livré (ou abandonné).

| ID | Lot | Statut | Délégable | Zone |
|---|---|---|---|---|
| L01 | Socle vide : gabarits officiels Django et Vue, outillage, CI ([0002](decisions/0002-socle-minimal-officiel.md), [0004](decisions/0004-demarrer-d-un-socle-vide.md)) | livré | non | tout |
| L02 | Les opérations de bout en bout : modèle, données fictives, admin, API, carte, bandeau, test dans le navigateur | prêt | oui | `backend/operations/`, `frontend/src/` |
| L03 | Fiche complète d'une opération | à définir | oui | `frontend/src/components/`, `backend/operations/` |
| L04 | Chiffres clés | à définir | oui | `frontend/src/components/`, `backend/operations/views.py` |
| L05 | Filtre par dates et histogramme par mois | à définir | oui | `frontend/src/components/`, `backend/operations/views.py` |
| L06 | Légende complète et couches (ports, régions SAR, eaux territoriales) | à définir | oui | `frontend/src/views/`, `frontend/public/` |
| L07 | Fonds de carte libres (PMTiles), dont satellite ou perte assumée | à définir | oui | `frontend/public/`, `frontend/src/views/` |
| L08 | Allemand et italien | à définir | oui | `frontend/src/` (vue-i18n à ajouter) |
| L09 | Entête : glossaire, journal de bord, don ; contributeurs | à définir | oui | `frontend/src/views/` |
| L10 | Visite guidée | à définir | partiel | `frontend/src/components/` |
| L11 | Mobile : menu, chiffres compacts | à définir | oui | `frontend/src/views/` |
| L12 | Outillage : robots et contrôles en plus de la CI et de pre-commit, une issue chacun | prêt | oui | `.github/` |
| L13 | Image de production et CI (CI faite, reste l'image) | prêt | oui | `.github/workflows/`, déploiement |

## Fini, pour chaque lot

- Les tests du lot passent (`uv run manage.py test`, `pnpm test:unit --run`, et
  `pnpm test:e2e` si le lot touche un parcours).
- Les vérifications de `TECHNICAL.md` sont vertes (backend et frontend).
- Couleurs et espacements issus des jetons ; textes en anglais et en français une fois le lot L08 livré.
- Aucune ligne de code CartONG ; la colonne « Ici » de `docs/parite-cartong.md` est mise à jour.

Le détail de chaque lot prêt est dans ses issues.
