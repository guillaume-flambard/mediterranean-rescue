# Parité avec la carte CartONG

Ce que fait la carte actuelle (map.sosmediterranee.org, code `CartONG/SOSMedDashboard`), relevé le
30/10/2026 dans son interface et ses traductions. C'est le cahier des charges : on reproduit le
comportement, jamais le code (pas de licence, voir la décision 0001).

| Écran ou fonction | Chez CartONG | Ici | Lot |
|---|---|---|---|
| Carte des opérations, une couleur par type | Mapbox, icônes par type | MapLibre, cercles d'une seule couleur | L06 |
| Fiche d'une opération au clic | fenêtre par type : opération, incident, naufrage, morts et disparus ; vent, vagues, embarcation, port de débarquement, photos et vidéos, témoignages | non | L03 |
| Chiffres clés | opérations, survivants, jours d'opération, « depuis » ; femmes, hommes, mineurs, mineurs non accompagnés, enfants de moins de 5 ans, femmes enceintes, nationalités | non | L04 |
| Filtre par dates | curseur de période et histogramme « opérations par mois » | non | L05 |
| Légende et couches | sauvetage, transfert, évacuation médicale, naufrage, incident, morts et disparus, ports, régions de recherche et sauvetage, eaux territoriales ; chaque entrée avec sa définition | non | L06 |
| Fonds de carte | trois fonds Mapbox : SOS, satellite, sombre | un fond clair servi par l'app | L07 |
| Langues | allemand, anglais, français, italien | anglais | L08 |
| Entête | titre, glossaire, lien vers le journal de bord, appel au don | titre et nombre d'opérations | L09 |
| Contributeurs | bénévoles et équipe CartONG, développeurs | non | L09 |
| Visite virtuelle | parcours guidé | non | L10 |
| Mobile | menu burger, chiffres clés compacts | entête puis carte, empilés | L11 |

Ce que la carte CartONG ne fait pas et qu'on garde : chaque chiffre a une source, rien n'est publié
sans relecture, inconnu n'est jamais zéro, aucune clé d'API dans la page.
