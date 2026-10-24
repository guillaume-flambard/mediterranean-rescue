# Catalogue des données existantes

Inventaire vérifié le 24 octobre 2026. Contrats observés dans le code public, pas dictionnaire validé par l’association. Aucune base opérationnelle copiée dans ce fork. La disponibilité technique d’un CSV ne donne pas un droit de republication.

## Systèmes existants

| Source | Ce qui est observé | Accès / fraîcheur | Droit de réutilisation |
| --- | --- | --- | --- |
| [Carte SOS](https://map.sosmediterranee.org/) | Application Vue 3 / TypeScript / Mapbox GL | Page publique HTTP 200 ; fréquence non contractuelle | Non établi |
| [Code CartONG](https://github.com/CartONG/SOSMedDashboard) | Adaptateurs Sheets et référentiels locaux | main c5f4e9a2e52da3e5877da0bd0e8d5e45df789135, 28/03/2024 | API GitHub license:null ; ne pas recopier sans clarification |
| Sheets Data_operations / Other_data / Data_ports | Source tabulaire consommée par la carte | API v4 dans code ; CSV gviz public vérifié sans clé sur un petit échantillon, sans sauvegarde du dataset | Propriétaire et licence à confirmer |
| [Archive du journal](https://www.sosmediterranee.org/operation-archived/) | Voyages, ports, effectifs et chronologie | Entrées visibles jusqu’à août 2026 ; HTML, pas d’API contractuelle vérifiée | Non établi |
| [Rapports SOS France](https://sosmediterranee.fr/publications/) | Rapports 2016 à 2025 et dossiers | Documents publics, cadence annuelle des rapports | Non établi |
| [Dépôt Data for Good](https://github.com/dataforgoodfr/mediterranean-rescue) | Template Python, pas de données métier observées | Création 06/10/2026 | MIT pour le code de ce dépôt |

## Data_operations

Source du contrat : [OpsData.ts](https://github.com/CartONG/SOSMedDashboard/blob/main/src/classes/data/OpsData.ts). Toutes les cellules sont reçues comme texte. Les types ci-dessous sont ceux à normaliser et valider.

| Colonnes exactes | Sens / format observé | Traitement cible |
| --- | --- | --- |
| date | DD/MM/YYYY, sans heure ni fuseau | Date seule, ne pas inventer une heure UTC |
| type_ops | Rescue, Transfer, Medevac | Enum métier ; conserver valeur source |
| nb_ops | Numérique attendu | Définition à confirmer, pas un identifiant démontré |
| nb_survivor | Effectif | Entier nullable, ne pas sommer transferts et sauvetages comme personnes uniques |
| male, female | Effectifs agrégés | Entiers nullables, définitions à confirmer |
| under_18, under_18_unacc, under_5 | Effectifs d’âge | Valeurs emboîtées, non additives |
| pregnant_women | Effectif | Recouvre potentiellement female, aucune somme automatique |
| latitude, longitude | Coordonnées texte, degrés/minutes possibles | Parseur explicite, précision, rejet de l’ambiguïté |
| wind_force | Numérique attendu | Unité à confirmer |
| wave_height | Décimal, virgules observées | Décimal, ne pas reproduire parseInt historique |
| boat_type | Catégorie d’embarcation | Référentiel/valeur source |
| nb_nationalities | Entier attendu, non utilisé par adaptateur | Vérifier cohérence avec liste, pas de déduction |
| type_nationalities | Liste libre séparée par ; | Liste normalisée ; nom historique nbNationalities trompeur |
| transfer_type | Texte | Mapping explicite avec divergence historique transfertType |
| Port_disembarkation | Nom libre, casse de colonne exacte | Port et alias approuvé, pas de fuzzy join silencieux |
| image_src, video_srv | Listes d’URL séparées par ; | Liens contrôlés, pas d’aspiration ni republication automatique |
| testimony_name, testimony_src | Listes parallèles séparées par ; | Objets label/url, validation des tailles et droits |

Pas de event_id stable, voyage_id, source_id ni navire dans cet onglet. Le numéro de ligne est une localisation de snapshot, pas une identité. Colonnes terminales vides observées : ignorer seulement si entièrement vides, sinon signaler une dérive.

## Other_data

Contrat : [OtherData.ts](https://github.com/CartONG/SOSMedDashboard/blob/main/src/classes/data/OtherData.ts).

- date : code attend DD-MM-YYYY, différent de Data_operations.
- type : Shipwreck, Dead & Missing, Incident.
- latitude / longitude : coordonnées texte.
- wind_force / wave_height : numériques à normaliser ; ancien GeoJSON les laisse comme texte.
- boat_type, inc_action, boat_involved : textes métier à qualifier.
- death_nb_people : effectif décès/disparitions, définition et niveau de certitude à confirmer.
- shipwreck_nb : valeur numérique, sémantique à confirmer.
- testimony_name / testimony_src / image_src / video_srv : listes texte séparées par ;.

Ne pas fusionner un incident avec un sauvetage proche sans correspondance validée. Les morts/disparus et les rescapés ne sont pas une partition exhaustive des personnes exposées.

## Data_ports et référentiels cartographiques

[Harbors.ts](https://github.com/CartONG/SOSMedDashboard/blob/main/src/classes/data/Harbors.ts) consomme nom, latitude, longitude. Aucun code de port normalisé n’est fourni dans cet onglet. Le Store charge ce tableau, pas nécessairement le GeoJSON local.

Dans [src/assets/resources](https://github.com/CartONG/SOSMedDashboard/tree/main/src/assets/resources) : SAR.json (3 MultiLineString), SAR_centers.json (3 Point), zones_12_miles.json (25 Polygon), harbors_mediterranee.json (254 ports avec codes/catégories et métadonnées variables). L’existence de ces fichiers ne démontre pas leur autorité, leur date d’effet ou leurs droits. Un champ source:null est observé dans le référentiel de ports. Aucune copie incluse dans le fork.

## Journal de bord et liaisons futures

[Exemple de voyage du 14 au 22 août 2026](https://www.sosmediterranee.org/operation/operation-14-22-august-2026/) : chronologie date/heure, communications, coordonnées compactes et narratives, estimations puis corrections d’effectifs. Une incohérence de date entre une entrée et la période du titre est observable : conserver la valeur source et exiger une revue.

Modèle cible : voyage → événements → entrées de journal ; événement → preuves et révisions d’effectifs. L’URL officielle est le premier lien utile. La jointure date/effectif/proximité n’est qu’une proposition de rapprochement à valider. Ne pas produire de position exacte depuis un récit approximatif.

## Flux de migration retenu

1. Obtenir l’autorisation et un snapshot/version du fichier ; sauvegarder l’empreinte, contrat, onglet, numéro de ligne et valeur source dans un espace privé.
2. Normaliser sans perte et produire un rapport d’anomalies : date, position, décimal, valeur inconnue et colonnes nouvelles.
3. Construire un crosswalk approuvé vers UUID internes et alias de ports. Les corrections d’une ligne existante créent une révision, pas une nouvelle identité improvisée.
4. Valider le lot et les liens, puis publier explicitement les champs autorisés. Une erreur ne doit pas publier une partie du lot.
5. Rejouer le même snapshot sans doublon ; conserver l’audit et permettre le retrait. Une suppression dans Sheets ne supprime pas silencieusement une publication.

Les calculs historiques de [PopUpAndStats.ts](https://github.com/CartONG/SOSMedDashboard/blob/main/src/classes/PopUpAndStats.ts) additionnent notamment effectifs et nb_ops ; les filtres du Store et de la carte suivent des chemins distincts. La nouvelle API doit partager le même filtre pour carte/liste/agrégats et donner un nom honnête à chaque mesure. Les inconnus historiques transformés en zéro à l’affichage ne sont pas une règle à reprendre.

## Informations à demander lundi

Propriétaire/éditeur Sheets, volume et date maximale réels, définition de chaque colonne, identités et éventuels fichiers plus récents, licence/autorisation par champ, règles de précision et publication, rôle de l’existant CartONG, référent pour valider les correspondances et corrections. L’accès en écriture à leur système n’est pas nécessaire pour développer nos contrats sur des fixtures indépendantes.
