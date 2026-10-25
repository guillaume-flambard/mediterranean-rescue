# Vocabulaire de l'interface

Décidé le 24 octobre 2026 après le retour de Guillaume : « une ligne, une row, ça ne veut rien dire ». Règle : un humain qui n'est jamais venu sur le site doit comprendre chaque mot, et un bénévole qui maintient les données aussi. Le terme technique ne s'affiche jamais seul ; quand il est utile (pour retrouver une donnée dans Google Sheets), il vient en aide, formulé comme une indication pratique.

## Ce que font les sites comparables

- **Carte SOS MEDITERRANEE (CartONG)** : un point par opération ; un clic ouvre une « fiche » avec la date, le type d'embarcation, le nombre et le type de personnes secourues, le port de débarquement, des photos et vidéos ; filtres par période et légende. Aucun identifiant technique visible. [CartONG](https://www.cartong.org/en/2024/02/14/an-interactive-map-to-shed-light-on-sos-mediterranees-rescue-operations/)
- **Missing Migrants Project (OIM)** : l'unité est l'« incident » ; les chiffres sont présentés comme des « estimations minimales », les lieux comme « approximatifs » ; la fraîcheur est dite en clair (« dernier incident enregistré le … »). [IOM](https://missingmigrants.iom.int/data)
- **ACLED** : un identifiant d'événement stable existe, mais il sert à l'export et à la citation, pas à la lecture ; chaque événement porte sa source. [ACLED codebook](https://acleddata.com/methodology/acled-codebook)
- **Our World in Data** : chaque graphique indique sa source et propose « Learn more about this data » ; les transformations sont signalées en toutes lettres. [OWID FAQ](https://ourworldindata.org/faqs)

Conclusion : on parle d'opérations et d'événements, on dit d'où vient chaque chiffre et à quel point il est sûr, et on cache la mécanique (lignes, exports, identifiants) derrière une phrase utile.

## Public

| Interne | Affiché (EN) | Affiché (FR) |
| --- | --- | --- |
| event, row d'opération | Rescue operation, Transfer… | Opération de sauvetage, Transfert… |
| nb_survivor | 110 people rescued (selon le type : transferred, evacuated, involved) | 110 personnes secourues (transférées, évacuées, concernées) |
| source | Source: SOS MEDITERRANEE | Source : SOS MEDITERRANEE |
| precision approximate | approximate position | position approximative |
| hemisphere inferred | position estimated (hemisphere not written in the source) | position estimée (hémisphère absent de la source) |

## Équipe (connectée)

| Interne | Affiché (EN) | Affiché (FR) |
| --- | --- | --- |
| private preview | Team view | Vue équipe |
| public mode | Public view | Vue publique |
| snapshot, export | data update of {date} | mise à jour du {date} |
| Data_operations / Other_data / Data_ports | rescue operations sheet / other events sheet / ports list | tableur des opérations / tableur des autres événements / liste des ports |
| row N | "In Google Sheets: row N of the rescue operations sheet" (dans la fiche ouverte seulement) | « Dans Google Sheets : ligne N du tableur des opérations » |
| to_review | Not verified yet | Pas encore vérifié |
| blocked | To fix in the sheet | À corriger dans le tableur |
| linked | Verified | Vérifié |
| identity | the event (as followed from one update to the next) | l'événement (suivi d'une mise à jour à l'autre) |
| create_identity | This is a new event | C'est un nouvel événement |
| link | Same event as one already verified | Même événement qu'un déjà vérifié |
| exact carry | unchanged since the last update | inchangé depuis la dernière mise à jour |

Les noms techniques (Data_operations, identité, rattachement) restent dans le code, les décisions d'architecture et les journaux ; ils n'apparaissent pas comme libellés d'écran.
