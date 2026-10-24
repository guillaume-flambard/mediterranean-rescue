# Diagnostic de l’onglet Data_ports

> **Données synthétiques.** Fichier fictif écrit pour les tests : ce rapport ne dit rien de la qualité du vrai jeu de données.

- Empreinte SHA-256 du snapshot : `12eb3acc1b8041e1cdae65aebaad3a66a91bdf56f001d0041e71aaadad6e8bbc` (95 octets, BOM UTF-8 : oui)
- Contrat : `sheets-observed-v1` (observed_not_association_approved)
- Lecture du CSV : complète : tout le fichier a été lu et se termine par une fin de ligne
- Normalisation : bloquée par au moins une erreur
- Identités : non résolues ; un numéro de ligne localise le snapshot, pas un événement
- Publication : désactivée ; cet outil ne crée ni événement ni brouillon

| Enregistrements lus | Lignes diagnostiquées | Lignes vides ignorées | Erreurs de fichier | Lignes en erreur | Lignes avec avertissement | Erreurs | Avertissements |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 3 | 0 | 0 | 1 | 0 | 1 | 0 |

## Contrôles déclenchés

| Code | Occurrences | Signification |
| --- | ---: | --- |
| `missing_cells` | 1 | Moins de cellules que d’en-têtes ; ligne non normalisée. |

## Localisation

Ligne physique de début dans le snapshot ; colonne numérotée à partir de 1.

| Niveau | Ligne | Colonne | Champ du contrat | Code |
| --- | ---: | ---: | --- | --- |
| error | 4 |  |  | `missing_cells` |

## Limites

- Le contrat vient du code CartONG et de l’export du 24 octobre 2026 ; il n’est pas approuvé par l’association.
- L’hémisphère absent n’est déduit que si une seule lecture tombe dans la région du contrat ; cette règle est une proposition à valider.
- Unités, définitions des compteurs et marqueurs d’inconnu restent à valider.
- Les cellules originales sont dans `diagnostic.json` et `snapshot.csv`, privés.
