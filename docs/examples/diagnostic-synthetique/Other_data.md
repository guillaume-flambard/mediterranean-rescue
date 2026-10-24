# Diagnostic de l’onglet Other_data

> **Données synthétiques.** Fichier fictif écrit pour les tests : ce rapport ne dit rien de la qualité du vrai jeu de données.

- Empreinte SHA-256 du snapshot : `73cc47dbd5bbe434ce31c25e9ebe3ba3277fd8259e40b01eb5d79bf31b8d43ca` (414 octets, BOM UTF-8 : non)
- Contrat : `sheets-observed-v1` (observed_not_association_approved)
- Lecture du CSV : complète : tout le fichier a été lu et se termine par une fin de ligne
- Normalisation : bloquée par au moins une erreur
- Identités : non résolues ; un numéro de ligne localise le snapshot, pas un événement
- Publication : désactivée ; cet outil ne crée ni événement ni brouillon

| Enregistrements lus | Lignes diagnostiquées | Lignes vides ignorées | Erreurs de fichier | Lignes en erreur | Lignes avec avertissement | Erreurs | Avertissements |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 4 | 4 | 0 | 0 | 2 | 1 | 5 | 1 |

## Contrôles déclenchés

| Code | Occurrences | Signification |
| --- | ---: | --- |
| `coordinate_out_of_range` | 2 | Coordonnée hors des bornes, comparée exactement avant conversion. |
| `date_format_of_other_sheet` | 1 | Date au format de l’autre onglet ; non convertie. |
| `impossible_date` | 1 | Date qui n’existe pas au calendrier. |
| `missing_position` | 1 | Position inconnue ; aucun point de remplacement. |
| `unnamed_column_has_value` | 1 | Valeur dans une colonne sans en-tête. |

## Localisation

Ligne physique de début dans le snapshot ; colonne numérotée à partir de 1.

| Niveau | Ligne | Colonne | Champ du contrat | Code |
| --- | ---: | ---: | --- | --- |
| warning | 4 | 3 | latitude | `missing_position` |
| error | 5 | 16 |  | `unnamed_column_has_value` |
| error | 5 | 1 | date | `date_format_of_other_sheet` |
| error | 6 | 1 | date | `impossible_date` |
| error | 6 | 3 | latitude | `coordinate_out_of_range` |
| error | 6 | 4 | longitude | `coordinate_out_of_range` |

## Limites

- Le contrat est observé dans le code CartONG, pas approuvé par l’association. Les noms d’en-tête d’Other_data et Data_ports ne sont pas confirmés par ce code, qui les lit par position.
- Unités, définitions des compteurs et marqueurs d’inconnu restent à valider.
- Les cellules originales sont dans `diagnostic.json` et `snapshot.csv`, privés.
