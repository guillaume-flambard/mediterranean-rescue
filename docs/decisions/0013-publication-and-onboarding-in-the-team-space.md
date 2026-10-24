# ADR 0013 : publier depuis l'espace équipe, accueillir les nouveaux venus, identité propre

Statut : proposé le 24 octobre 2026, à la demande de Guillaume (« imagine que demain SOS MEDITERRANEE arrive là-dessus, avec des bénévoles et des bénévoles admin qui ne connaissent pas grand-chose, et qui doivent s'y retrouver »). Complète l'ADR 0012.

## Constat
Le parcours qui fait réussir le projet (PRODUCT.md) va d'une source autorisée à un événement publié, puis retiré si besoin. Avant cette décision, la vérification se faisait dans l'espace équipe mais la préparation des brouillons n'avait pas d'écran et la publication passait par l'administration Django, en anglais technique, avec un motif fixe. Un ou une bénévole ne pouvait pas finir le parcours seul.

## Décision
- **Publier dans l'espace équipe**, en deux décisions nommées, chacune avec un motif :
  - « Préparer » : `POST /api/private/v1/publication/prepare/` appelle `drafts.create_drafts` sur la dernière copie de chaque onglet d'événements, en une transaction.
  - « Publier » ou « Retirer » : `POST /api/private/v1/publication/decisions/` (1 à 100 événements, tout ou rien) appelle `services.set_publication` pour chacun. Le service reste le seul à vérifier la permission `publish_event`, les droits de la source, le motif et à écrire l'audit.
  - Lecture : `GET /api/private/v1/publication/` (ce qui est prêt, en attente, à corriger, droits par source, rôles) et `GET /api/private/v1/publication/events/?status=`.
  - Un refus pour droits non enregistrés a son code, `rights_not_approved`, pour que l'écran l'explique au lieu d'un « conflit ».
- **Le verrou de droits reste.** Tant que `Source.rights_approved` est faux, l'écran dit pourquoi on ne peut pas publier et qui le débloque (l'accord écrit de l'association, enregistré dans l'administration par un superutilisateur). Le fork n'a pas cet accord : la base locale reste verrouillée.
- **Accueil de l'équipe** (`/workspace`) : une liste « À faire » dans l'ordre du travail (lecture du tableur, vérifier, préparer, publier), chaque étape avec une phrase « à quoi ça sert », un état en mots (À faire, Fait, Pas encore possible) et un seul bouton ; un message de bienvenue qu'on peut fermer ; le rôle de la personne en clair. Modèle : liste de tâches GOV.UK, états vides qui enseignent (NN/g).
- **Accueil du public** : une page « À propos des données » (`/about`) sur le modèle de l'OIM Missing Migrants et d'Our World in Data (ce qu'il faut savoir, comment lire la carte, définitions de travail, de la mer à la page, dignité, citer et réutiliser, autres sources) ; une carte « Première visite » qu'on peut fermer ; un état vide qui dit pourquoi rien n'est publié.
- **Identité propre** : une marque dessinée pour le projet (un point documenté au-dessus de la mer), favicon, icônes d'application et image de partage. Pas de logo ni de photo de SOS MEDITERRANEE : la recherche du 24 octobre 2026 n'a trouvé aucune licence (mentions légales sans clause, médias presse « usage éditorial » seulement, marque déposée). Le nom de l'association n'apparaît qu'en texte, pour dire d'où viennent les données et que le site n'est pas officiel.

## Sources
GOV.UK Design System, « Complete multiple tasks » et « Check answers » ; NN/g sur les états vides et les dialogues de confirmation ; OIM Missing Migrants Project (méthodologie) ; FAQ et glossaire de SOS MEDITERRANEE (« rescapés ») ; mentions légales de sosmediterranee.fr.

## Limites
- Les définitions publiques sont « de travail » et doivent être confirmées avec SOS MEDITERRANEE.
- Une correction d'un événement déjà préparé (`revision_needed`) est comptée mais pas encore traitée dans l'espace équipe (le service `revisions` existe, l'écran non).
- L'image de partage utilise un chemin relatif tant que le site n'a pas de domaine.
