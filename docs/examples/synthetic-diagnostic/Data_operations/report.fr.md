# Diagnostic de l’onglet Data_operations

> **Données synthétiques.** Fichier fictif écrit pour les tests : ce rapport ne dit rien de la qualité du vrai jeu de données.

- Empreinte SHA-256 du snapshot : `ac7e593d2071491bf742a8243d6b65b8538ed33b8cfc360941f4eb0e7a4cca65` (1096 octets, BOM UTF-8 : non)
- Contrat : `sheets-observed-v1` (observed_not_association_approved)
- Lecture du CSV : complète : tout le fichier a été lu et se termine par une fin de ligne
- Normalisation : bloquée par au moins une erreur
- Identités : non résolues ; un numéro de ligne localise le snapshot, pas un événement
- Publication : désactivée ; cet outil ne crée ni événement ni brouillon

| Enregistrements lus | Lignes diagnostiquées | Lignes vides ignorées | Erreurs de fichier | Lignes en erreur | Lignes avec avertissement | Erreurs | Avertissements |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 8 | 7 | 1 | 0 | 4 | 3 | 11 | 4 |

## Contrôles déclenchés

| Code | Occurrences | Signification |
| --- | ---: | --- |
| `coordinate_minutes_out_of_range` | 1 | Minutes d’arc égales ou supérieures à 60. |
| `coordinate_out_of_range` | 1 | Coordonnée hors des bornes, comparée exactement avant conversion. |
| `coordinate_pair_incomplete` | 1 | Une seule des deux coordonnées est connue. |
| `date_format_of_other_sheet` | 1 | Date au format de l’autre onglet ; non convertie. |
| `exact_duplicate_row` | 1 | Ligne identique à une ligne précédente ; signalée, jamais fusionnée. |
| `fractional_count` | 1 | Effectif non entier. |
| `impossible_date` | 1 | Date qui n’existe pas au calendrier. |
| `missing_position` | 1 | Position inconnue ; aucun point de remplacement. |
| `negative_count` | 1 | Effectif négatif. |
| `subpopulation_exceeds_total` | 2 | Sous-population supérieure à son total ; à revoir, rien n’est corrigé. |
| `testimony_lists_misaligned` | 1 | Listes de témoignages de longueurs différentes ; aucune paire devinée. |
| `unknown_kind` | 1 | Catégorie hors contrat ; valeur source conservée. |
| `unsafe_url_scheme` | 1 | Lien hors http/https refusé. |
| `url_with_credentials` | 1 | Lien contenant des identifiants refusé. |

## Localisation

Ligne physique de début dans le snapshot ; colonne numérotée à partir de 1.

| Niveau | Ligne | Colonne | Champ du contrat | Code |
| --- | ---: | ---: | --- | --- |
| error | 4 | 1 | date | `impossible_date` |
| warning | 4 | 11 | latitude | `missing_position` |
| error | 5 | 3 | nb_ops | `negative_count` |
| error | 5 | 4 | nb_survivor | `fractional_count` |
| error | 5 | 20 | image_src | `unsafe_url_scheme` |
| error | 5 | 23 | testimony_src | `testimony_lists_misaligned` |
| error | 5 | 11 | latitude | `coordinate_out_of_range` |
| warning | 5 | 8 | under_18_unacc | `subpopulation_exceeds_total` |
| warning | 5 | 9 | under_5 | `subpopulation_exceeds_total` |
| error | 6 | 1 | date | `date_format_of_other_sheet` |
| error | 6 | 2 | type_ops | `unknown_kind` |
| error | 6 | 20 | image_src | `url_with_credentials` |
| error | 6 | 11 | latitude | `coordinate_minutes_out_of_range` |
| warning | 7 |  |  | `exact_duplicate_row` |
| error | 9 | 12 | longitude | `coordinate_pair_incomplete` |

## Limites

- Le contrat vient du code CartONG et de l’export du 24 octobre 2026 ; il n’est pas approuvé par l’association.
- L’hémisphère absent n’est déduit que si une seule lecture tombe dans la région du contrat ; cette règle est une proposition à valider.
- Unités, définitions des compteurs et marqueurs d’inconnu restent à valider.
- Les cellules originales sont dans `diagnostic.json` et `snapshot.csv`, privés.
