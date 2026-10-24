# Exemple synthétique du diagnostic

**Fichiers fictifs.** Ces trois rapports ont été produits à partir des fixtures écrites à la main dans `backend/catalog/tests/fixtures/sheets/`. Elles contiennent des anomalies volontaires et ne disent rien de la qualité du vrai jeu de données de SOS MEDITERRANEE.

Reproduire (dossiers de sortie neufs, jamais écrasés) :

```sh
for sheet in Data_operations Other_data Data_ports; do
  python3 scripts/diagnose_sheets.py --sheet "$sheet" --synthetic \
    --input "backend/catalog/tests/fixtures/sheets/synthetic-$sheet.csv" \
    --output-dir "data/local/demo-diagnostic/$sheet"
done
```

Chaque commande sort avec le code 3 : le paquet est écrit et la normalisation est bloquée par les anomalies volontaires. Seul `rapport.md` est recopié ici ; `diagnostic.json` et `snapshot.csv` restent dans `data/local`, ignoré par Git. Le diagnostic est déterministe : mêmes octets, même empreinte et même rapport.
