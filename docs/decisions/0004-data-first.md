# ADR 0004 : la donnée d'abord, diagnostic hors ligne des exports Sheets

Statut : accepté par Guillaume le 24 octobre 2026 pour la première tranche donnée. L'interface existante est conservée telle quelle ; Base UI reste le choix de la future application.

## Décision
Avant tout connecteur réseau ou import réel, chaque export CSV des onglets Data_operations, Other_data et Data_ports passe par un diagnostic privé et reproductible : contrat machine lisible (`contracts/sheets-v1.json`), valeurs candidates normalisées, provenance exacte et anomalies. Le diagnostic ne crée aucun événement, brouillon ni publication et n'écrit dans aucune base.

## Constat qui change l'inventaire
Au commit CartONG `c5f4e9a2`, `OpsData.ts` lit Data_operations par nom d'en-tête, mais `OtherData.ts` et `Harbors.ts` lisent Other_data et Data_ports **par position** et jettent la ligne d'en-tête. Les noms d'en-tête de ces deux onglets viennent donc de l'inventaire du dossier, pas du code : le diagnostic signale tout ordre qui diffère de celui de la carte existante. De même, `OpsData.ts` lit `transfertType` (en-tête `transfert_type`) alors que l'inventaire donne `transfer_type` : aucun alias n'est appliqué. L'export du 24 octobre 2026 a tranché ces deux points (section suivante).

## Constats sur l'export public du 24 octobre 2026
Sur décision de Guillaume, les trois onglets ont été téléchargés une fois en CSV pour un diagnostic local et privé (`data/local`, hors Git, sans médias ni republication). Faits établis :
- Tous les noms d'en-tête du contrat sont présents à l'identique, dont `transfer_type` et `nom`. La carte CartONG lit `transfertType` et ne reçoit donc jamais cette valeur.
- Data_operations porte trois colonnes finales sans en-tête mais remplies : l'une copie `type_nationalities` (369 lignes sur 370), les deux autres sont identiques entre elles. Elles sont signalées une fois par colonne et conservées brutes.
- Les dates d'Other_data utilisent la barre oblique, jour en premier, comme Data_operations, alors que le code CartONG attend des tirets.
- Les coordonnées sont en degrés et minutes **sans hémisphère** (`35° 30.5`). Un hémisphère par défaut serait faux : la longitude de Valence, à l'ouest de Greenwich, est écrite `0° 18.59`. La règle retenue, proposée et non validée, ne résout une valeur que si une seule lecture signée tombe dans une boîte méditerranéenne grossière (latitude 30 à 46, longitude -6 à 36,5) ; sinon `hemisphere_ambiguous` et aucune position.
- `nb_nationalities` n'est pas la longueur de la liste `type_nationalities` (égalité dans 42 lignes sur 259) : la relation a été retirée du contrat, la définition reste inconnue.
- L'export Google ne se termine pas par une fin de ligne : la lecture est donc `end_unverified` par construction. La complétude doit venir de la provenance du téléchargement, pas du fichier.

## Règles retenues
- Entrée : UTF-8 avec BOM accepté, virgule, guillemets RFC 4180 vérifiés avant lecture ; 5 Mio et 10 000 enregistrements au plus.
- Correspondance des colonnes par nom exact ; en-tête dupliqué, colonne inconnue, ligne trop courte ou trop longue sont des erreurs ; une colonne anonyme non vide est un avertissement, une fois par colonne. Une ligne mal formée garde ses cellules brutes et n'est pas normalisée (aucun décalage).
- Inconnu (vide, `n/a`, `unknown`, `inconnu`, `?`, `-`, liste proposée) devient `null`, jamais zéro.
- Coordonnées : décimal, degrés et minutes avec hémisphère explicite, ou sans hémisphère selon la règle de région ci-dessus ; bornes comparées en valeur exacte (`Fraction`) avant toute conversion ; les formats compacts restent refusés.
- Liens : http et https seulement, sans identifiants ; aucun téléchargement. Paires de témoignages seulement si les listes sont alignées.
- Provenance : `Onglet@sha256:<empreinte>#L<ligne physique>` ; c'est une localisation de snapshot, pas une identité. Les doublons exacts sont signalés, jamais fusionnés.
- Statuts séparés : lecture du CSV (`complete`, `end_unverified`, `partial`, `rejected`), normalisation (`blocked`, `needs_review`), identités (`unresolved`), publication (`disabled`). Le paquet de sortie n'est complet que si `MANIFEST.json` existe.
- Sorties privées : nouveau dossier jamais écrasé, `0700` et fichiers `0600`, `.gitignore` local écrit en premier ; rapport Markdown sans valeur source.

## Conséquences
Le module `backend/catalog/sheets.py` n'utilise que la bibliothèque standard : il tourne sur l'hôte sans Docker et ses tests sont aussi exécutés par la suite Django en CI. Brancher ce diagnostic sur le staging métier, le crosswalk d'identités et les alias de ports reste la tranche suivante, après validation d'un extrait autorisé.
