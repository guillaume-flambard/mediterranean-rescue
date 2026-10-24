# Recette de la tranche REST

1. Lire docs/PROJECT.md : objectifs, stack et ordre des lots correspondent-ils au projet souhaité ?
2. Suivre README pour démarrer ; ouvrir http://127.0.0.1:5173/ ; carte et liste vide honnête apparaissent.
3. Changer le type, inverser une période puis réinitialiser ; vérifier le retour à l’exploration.
4. Consulter http://127.0.0.1:8010/api/v1/events/ et /api/v1/schema/ ; aucun staging ou audit dans l’API publique.
5. Recette positive de fiches/données métier : prévue dans L2 après extrait autorisé, ne pas prétendre qu’elle a déjà eu lieu.

Aucun déploiement, aucun import SOS et aucun message envoyé à l’association.

# Recette de la tranche donnée D (diagnostic hors ligne)

1. Lancer `python3 scripts/diagnose_sheets.py --sheet Data_operations --synthetic --input backend/catalog/tests/fixtures/sheets/synthetic-Data_operations.csv --output-dir data/local/recette-1` ; le code de sortie vaut 3.
2. Ouvrir `data/local/recette-1/rapport.md` : la mention synthétique, les statuts et les compteurs se comprennent-ils vite ?
3. Prendre une anomalie (ligne, colonne) et la retrouver dans `snapshot.csv` et `diagnostic.json`.
4. Relancer la même commande : refus sans modification. Vérifier qu’aucun événement n’existe dans l’administration.
5. Lire les limites et choisir le premier extrait réel à faire valider par le référent.
