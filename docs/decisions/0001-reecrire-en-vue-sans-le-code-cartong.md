# 0001. Réécrire la carte en Vue, sans reprendre le code existant

Date : 30 octobre 2026. Statut : en vigueur.

## Contexte

La carte publique de SOS MEDITERRANEE ([map.sosmediterranee.org](https://map.sosmediterranee.org/))
a été construite par CartONG (`CartONG/SOSMedDashboard`) : une app Vue 3.3 sur Vue CLI, avec
mapbox-gl, jQuery et un tableur Google Sheets comme base de données.

Ce dépôt n'a pas de licence. Sans licence, son code appartient à ses auteurs : on ne peut ni le
modifier et le publier, ni le confier à des bénévoles.

## Décision

- Une app Vue neuve, créée avec le gabarit officiel `create-vue`, qui reproduit le **produit**
  de la carte actuelle (écrans, parcours, vocabulaire, langues), sans aucune ligne de son code.
  Ce qu'elle fait est relevé dans le [cahier de parité](../parite-cartong.md).
- MapLibre GL et un fond de carte servi par l'app (Natural Earth, domaine public) : aucun service
  extérieur, aucune clé d'API.
- Une API Django, dont l'admin sert à relire chaque opération avant publication.

## Conséquences

- Le code de ce dépôt est libre (MIT) et peut être confié aux bénévoles.
- L'interface connue de SOS MEDITERRANEE et du public est reproduite écran par écran, lot par
  lot ([docs/lots.md](../lots.md)).
- Personne ne copie de code de `CartONG/SOSMedDashboard`, même un extrait.
