# ADR 0004 : la donnée d'abord, diagnostic hors ligne des exports Sheets

Statut : accepté par Guillaume le 24 octobre 2026 pour la première tranche donnée. L'interface existante est conservée telle quelle ; Base UI reste le choix de la future application.

## Décision
Avant tout connecteur réseau ou import réel, chaque export CSV des onglets Data_operations, Other_data et Data_ports passe par un diagnostic privé et reproductible : contrat machine lisible (`contracts/sheets-v1.json`), valeurs candidates normalisées, provenance exacte et anomalies. Le diagnostic ne crée aucun événement, brouillon ni publication et n'écrit dans aucune base.

## Constat qui change l'inventaire
Au commit CartONG `c5f4e9a2`, `OpsData.ts` lit Data_operations par nom d'en-tête, mais `OtherData.ts` et `Harbors.ts` lisent Other_data et Data_ports **par position** et jettent la ligne d'en-tête. Les noms d'en-tête de ces deux onglets viennent donc de l'inventaire du dossier, pas du code : le contrat les marque `dossier_inventory_unverified` et le diagnostic signale tout ordre qui diffère de celui de la carte existante. De même, `OpsData.ts` lit `transfertType` (en-tête `transfert_type`) alors que l'inventaire donne `transfer_type` : aucun alias n'est appliqué, le premier export autorisé tranchera.

## Règles retenues
- Entrée : UTF-8 avec BOM accepté, virgule, guillemets RFC 4180 vérifiés avant lecture ; 5 Mio et 10 000 enregistrements au plus.
- Correspondance des colonnes par nom exact ; en-tête dupliqué, colonne inconnue, colonne anonyme non vide, ligne trop courte ou trop longue sont des erreurs. Une ligne mal formée garde ses cellules brutes et n'est pas normalisée (aucun décalage).
- Inconnu (vide, `n/a`, `unknown`, `inconnu`, `?`, `-`, liste proposée) devient `null`, jamais zéro.
- Coordonnées : décimal ou degrés et minutes avec hémisphère explicite ; bornes comparées en valeur exacte (`Fraction`) avant toute conversion ; les formats compacts restent refusés.
- Liens : http et https seulement, sans identifiants ; aucun téléchargement. Paires de témoignages seulement si les listes sont alignées.
- Provenance : `Onglet@sha256:<empreinte>#L<ligne physique>` ; c'est une localisation de snapshot, pas une identité. Les doublons exacts sont signalés, jamais fusionnés.
- Statuts séparés : lecture du CSV (`complete`, `partial`, `rejected`), normalisation (`blocked`, `needs_review`), identités (`unresolved`), publication (`disabled`). Le paquet de sortie n'est complet que si `MANIFEST.json` existe.
- Sorties privées : nouveau dossier jamais écrasé, `0700` et fichiers `0600`, `.gitignore` local écrit en premier ; rapport Markdown sans valeur source.

## Conséquences
Le module `backend/catalog/sheets.py` n'utilise que la bibliothèque standard : il tourne sur l'hôte sans Docker et ses tests sont aussi exécutés par la suite Django en CI. Brancher ce diagnostic sur le staging métier, le crosswalk d'identités et les alias de ports reste la tranche suivante, après validation d'un extrait autorisé.
