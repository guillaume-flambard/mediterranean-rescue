# Contrats des composants à construire

Spécification, pas catalogue implémenté. @base-ui/react1.9.0 est installé ; ses exports publics ont été vérifiés. Les noms de composants projet et variantes ci-dessous sont proposés. Voir [fondations](system.md) et [parcours](user-flows.md).

## Inventaire et priorité

| ID | Composant projet proposé | Fondation | Variantes / anatomie | Priorité |
| --- | --- | --- | --- | --- |
| C01 | Button | Base UI Button | primary, secondary, quiet, danger ; sm/md/lg ; icône facultative, label, attente | P1 |
| C02 | TextField | Field + Input | Label, contrôle, aide, erreur ; optional, readonly, disabled, invalid | P1 |
| C03 | SelectField | Field + Select | Choix court et stable, trigger, liste, sélection | P1 |
| C04 | SearchCombobox | Field + Combobox | Choix de port/identité dans une liste longue, recherche, résultats, vide | P1 |
| C05 | ChoiceGroup | Fieldset + RadioGroup | Décision parmi options explicitement nommées | P1 |
| C06 | Checkbox | Checkbox / CheckboxGroup | Checked, unchecked, indeterminate ; sélection et portée visibles | P1 |
| C07 | Dialog | Dialog | Titre, description, contenu, fermer, actions | P1 |
| C08 | ConfirmationDialog | AlertDialog | Conséquence précise, récapitulatif, annuler, action engagée | P1 |
| C09 | NavigationDrawer | Drawer | Menu mobile ; distinct du détail métier sur route | P1 |
| C10 | Tabs | Tabs | Vues sœurs du même objet, pas étapes d’un formulaire | P1 |
| C11 | ContextMenuButton | Menu | Actions secondaires nommées ; action critique toujours explicite | P2 |
| C12 | Tooltip | Tooltip | Explication complémentaire sur hover et focus | P2 |
| C13 | Toast | Toast | Retour non critique, fermeture accessible, doublé d’un état durable | P2 |
| C14 | Disclosure | Accordion / Collapsible | Détails techniques/provenance à la demande | P1 |
| C15 | DataTable | Table HTML + Button + Checkbox | Caption, en-têtes, titre ouvrable, cellules, sélection, pagination | P1 |
| C16 | FilterBar | Field, Select, Input + boutons projet | Critères, compteur, filtres actifs, effacer | P1 |
| C17 | StatusLabel | HTML/CSS | Libellé + pictogramme éventuel + couleur sémantique | P1 |
| C18 | InlineMessage / ErrorSummary | HTML sémantique | Information, warning, error, success ; liens vers corrections | P1 |
| C19 | EmptyState | HTML + Button | Absence de données, aucun résultat, accès indisponible | P1 |
| C20 | FileInput | input type=file + Field | Bouton de sélection et zone de dépôt facultative | P1 |
| C21 | PendingState | role=status + Progress si progression réelle | Indéterminé par défaut, texte et étape connue | P1 |
| C22 | RecordComparison | Composition métier | Reçu / interprété / candidat, différences et provenance | P1 |
| C23 | ReviewActionBar | Form + Button | Décision, motif, enregistrer / enregistrer puis suivant | P1 |
| C24 | PublicationSummary | dl/table + Field + Button | Contenu public exact, droits, points bloquants et effet | P1 ultérieur |
| C25 | Pagination | nav HTML + Button/liens | Plage affichée, total connu, précédent/suivant | P1 |
| C26 | DateRange | Fieldset + champs date natifs | Début, fin, format/aide, validation de période | P1 |

Les composants P1 ultérieurs ne bloquent pas la première file de revue. La pagination, les tableaux, les messages et les patterns métier ne sont pas présentés comme des composants déjà fournis par Base UI.

## C01 — Boutons

Une action principale par zone de décision. md=44px ; sm=36px avec cible adaptée ; lg=48px. Primary : fond action sombre, texte blanc. Secondary : fond blanc, contour de contrôle, texte marine. Quiet : action secondaire sans masse visuelle. Danger : retrait ou action destructive explicitement nommée, jamais simple navigation.

États : hover, pressed, focus-visible, disabled et loading. En attente, conserver le label et la largeur utile, indiquer aria-busy lorsque pertinent et empêcher le double envoi. Un lien de navigation garde une sémantique de lien. L’icône d’un bouton sans texte visible a un nom accessible localisé ; les actions majeures gardent un texte visible.

## C02–C05 — Formulaires et décisions

Label permanent, aide courte, état requis/facultatif explicite. Aucun placeholder utilisé comme seul label. aria-describedby relie aide et erreur. Afficher les erreurs de saisie au blur ou à la soumission ; après première erreur, les actualiser à mesure que la saisie devient valide. Ne pas afficher une erreur dès l’arrivée dans un champ vide.

Pour un formulaire invalide soumis : résumé en haut, focus sur le résumé puis liens vers les contrôles ; mêmes messages près des champs. Les erreurs serveur et de permission sont distinctes des erreurs de format. Les champs readonly restent lisibles et sélectionnables ; disabled indique une action indisponible et n’est pas le seul endroit où expliquer pourquoi.

Select pour quelques catégories connues ; Combobox pour chercher parmi beaucoup de ports/identités. Afficher des résultats compréhensibles avec contexte, pas uniquement des UUID. Aucun premier résultat sélectionné silencieusement après une recherche. Prévoir clavier, chargement, aucun résultat, erreur de recherche, requête annulée et contenu long.

Le choix d’une identité se formule par RadioGroup : « Créer une nouvelle identité », « Relier à une identité existante », « Examiner plus tard ». Le dernier choix ne crée rien et ne compte pas comme validation. Les champs de motif apparaissent avec la décision qui les exige, sans masquer les informations indispensables.

## C06 / C15 — Sélection et tableaux

La case d’en-tête sélectionne uniquement les lignes éligibles de la page visible, avec un texte qui l’explique. Afficher « 12 selected on this page / 12 sélectionnées sur cette page ». Aucun « tout sélectionner » implicite sur un autre périmètre. Si filtres ou page changent, vider la sélection et l’annoncer ; ne pas maintenir une sélection invisible en première version.

Le titre de ligne est un lien/bouton dédié pour inspecter. Ne pas rendre toute la ligne cliquable au détriment des cases et liens. Tab rejoint les contrôles et le titre ; ne pas créer une grille de tableur avec raccourcis spéciaux sans besoin démontré. Compteurs alignés, texte long lisible à l’ouverture. Caption et en-têtes identifient le contexte et l’unité.

Tri global seulement si le serveur le supporte. La liste publique existante est ordonnée par date : ne pas proposer un tri de toute la base en triant seulement la page courante. Charger25 lignes par défaut, pagination bornée ; pas de scroll infini dans la file de décisions.

Une approbation groupée apparaît uniquement pour les reports exacts éligibles. Son récapitulatif donne nombre, portée et effet, puis exige le motif. Le serveur revérifie toutes les lignes à l’envoi. Si l’opération n’est pas atomique, un résultat par ligne est obligatoire ; l’interface ne montre jamais un succès global pour une réussite partielle.

## C07–C10 — Panneaux et fenêtres

Le détail métier a une URL adressable. Sur grand écran, cette route peut s’afficher comme inspecteur à côté de la liste ; sur petit écran, elle occupe la page. Le contexte de liste est restauré au retour. Un panneau non modal utilise une sémantique de région nommée, pas un piège à focus. Un Drawer/Dialog modal emploie la primitive et ses mécanismes de focus.

Dialog pour une tâche courte. AlertDialog pour une conséquence sensible. Titre et effet explicites ; action d’annulation prioritaire au focus lorsqu’un choix peut être destructif. Escape ferme une fenêtre modale quand cela n’abandonne pas une écriture déjà engagée ; en cas de saisie non soumise, demander si l’utilisateur veut la perdre. Fermer une attente n’annule pas une opération serveur : le préciser et permettre de retrouver l’état.

Restaurer le focus sur le déclencheur s’il existe encore, sinon sur une destination logique annoncée. Pas de cascade de modales pour relier une ligne et lire sa source. Tabs pour « Summary / Source » d’un même objet ; le parcours import→revue utilise des étapes et non des tabs.

## C16 / C26 — Filtres et période

Choix simples de statut appliqués immédiatement, avec compteur actualisé. Recherche textuelle après250–300ms de pause, annulation de l’ancienne requête et protection contre les réponses tardives. La période a un bouton « Apply dates / Appliquer les dates » pour ne pas recharger entre deux saisies ; période inversée refusée avant requête.

Afficher chaque filtre actif et une suppression individuelle. « Clear filters / Effacer les filtres » restaure le périmètre initial. Un changement de filtre remet la pagination au début. L’URL conserve les filtres publics ; les cellules privées et motifs ne s’y inscrivent pas.

Le déplacement de la carte ne filtre pas automatiquement la liste. Une action « Search this area / Rechercher dans cette zone » applique la bbox explicitement ; la carte conserve ensuite un repère de ce périmètre et un moyen de le retirer.

## C17–C21 — Statuts, erreurs et attente

Utiliser des mots, pas des couleurs seules : Blocked, Needs review, Linked, Draft, Published, Withdrawn, Unknown, Training data, avec traductions. Le statut de qualité de ligne, celui de lecture du fichier et celui de publication sont trois informations différentes.

Une erreur indique ce qui a échoué, si l’état de l’action est connu et l’étape de reprise. 403 : droits insuffisants, pas « aucun résultat ». 404 d’un événement public indisponible : le dire sans révéler qu’il existe en privé. Conflit de revue : afficher le nouvel état et demander une nouvelle décision, sans écraser un autre relecteur.

FileInput : bouton accessible de sélection, nom du fichier après choix, type/taille acceptés, changement et suppression avant envoi. Le drag-and-drop reste optionnel ; il n’est jamais le seul moyen. La lecture des exports reste privée et le serveur revérifie toutes les contraintes.

PendingState : texte « Analyzing file / Analyse du fichier » et progression indéterminée tant que le serveur ne donne pas une progression fiable. Un skeleton reflète la structure future et se masque aux lecteurs d’écran ; un message d’état décrit l’attente. Ne pas effacer des résultats déjà chargés à chaque filtre ; annoncer leur actualisation et éviter une action sur une sélection devenue périmée.

## C22–C24 — Décisions métier

RecordComparison montre la valeur reçue exacte en texte, son interprétation candidate, puis l’identité proposée et les différences utiles. Le contenu brut est affiché comme texte, jamais interprété comme HTML. Les URLs sont validées et les références restent accessibles. Le mot « proposition » reste visible jusqu’à approbation.

La correction d’une cellule source ne se fait pas dans ce comparateur : revenir à la source et charger un nouvel export, ou construire ultérieurement un vrai service de révision. L’exception explicitement prévue concerne la position d’un port saisie par le relecteur, conservée avec son origine selon ADR0005.

ReviewActionBar confirme la nature de la décision et son motif. Le bouton s’adapte : « Create identity / Créer l’identité » pour la création et « Approve link / Valider le lien » pour le rattachement. « Approve and next / Valider et ouvrir la suivante » attend la confirmation serveur avant de déplacer le focus. Aucun faux bouton « Undo / Annuler » si le backend ne permet pas de revenir sur une décision auditée : décrire le vrai parcours de correction.

PublicationSummary appartient à une tranche ultérieure. Il montre uniquement ce qui deviendra public, la source, les droits, la licence et les limites. « Publish event / Publier l’événement » nomme sa conséquence. L’accès à l’espace privé n’est pas une permission de publier.

## Critères transversaux de recette future

Clavier seul, Escape, retour du focus, lecteur d’écran, textes longs anglais/français, pluriels, état réseau lent/coupé, double clic, changement concurrent, reflow200%, fenêtres étroites et reduced-motion. Tous les textes produit passent par les catalogues. Tous les contrôles restent compréhensibles sans la carte et sans dépendre d’une couleur.

Sources : [Field](https://base-ui.com/react/components/field), [Select](https://base-ui.com/react/components/select), [Dialog](https://base-ui.com/react/components/dialog), [Quick start et catalogue](https://base-ui.com/react/overview/quick-start). Les usages proposés doivent être implémentés puis testés ; la présence des primitives n’assure pas l’accessibilité de l’assemblage.
