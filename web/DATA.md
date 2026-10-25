# Contrat JSON du démonstrateur

Un tableau d’objets, jusqu’à 2 000 événements et fichier de 2 Mio maximum.

| Champ | Contrat |
| --- | --- |
| id | Texte non vide, unique dans le fichier |
| date | Date valide YYYY-MM-DD, pas un horodatage |
| longitude | Nombre, de -6 à 40 inclus |
| latitude | Nombre, de 30 à 46 inclus |
| people | Entier connu de 0 à 10 000 |
| ship | Texte non vide |
| source | URL absolue HTTP ou HTTPS, sans identifiants |
| note | Texte non vide ; expliquer le caractère fictif |
| synthetic | Booléen true obligatoire |

Chaque texte a une longueur maximale de 2 000 caractères. Les champs supplémentaires ne sont pas conservés. Les coordonnées sont des degrés décimaux WGS84, longitude puis latitude. La boîte de validation est celle de la carte, sans contrôle terre/mer. Les sources déclarées ne sont ni vérifiées ni chargées automatiquement. example.org/demo dans les fixtures n’est pas une preuve de sauvetage.

Un tableau vide est accepté. Le remplacement est atomique ; si une seule ligne échoue, aucune ligne du fichier n’est appliquée. L’export contient les événements filtrés, ordonnés du plus récent au plus ancien, avec tous les champs du contrat. Les bornes de date sont inclusives. Une plage inversée affiche une erreur et aucun résultat.

L’adaptateur de données réelles est une prochaine étape après accord métier et juridique : conserver identifiants source et version, différencier date de sauvetage/date de publication, traiter effectifs ou positions inconnus comme inconnus, valider unité de comptage, précision publiable et autorisation de réutilisation. Ne pas dériver un point précis d’un récit approximatif.
