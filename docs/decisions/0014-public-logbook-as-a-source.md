# ADR 0014 : le journal de bord public comme source, pour remettre la carte de SOS à jour

Statut : proposé le 24 octobre 2026, à la demande de Guillaume (« il faut que l'on apporte quelque chose de nouveau et bon et qui résout leur problème »). Répond au premier scénario de `docs/EXECUTION-PRIORITIES-2026-10-24.md` : compléter la carte CartONG plutôt que la remplacer.

## Problème constaté
La carte publique de SOS MEDITERRANEE (CartONG) lit un tableur dont la dernière opération date du 6 février 2024. L'équipage, lui, continue d'écrire chaque rotation de l'Ocean Viking dans le journal de bord public de sosmediterranee.org. Les opérations manquantes existent donc, en phrases ; personne ne les recopie dans le tableur. Détail et rapprochement chiffré : [backfill-2024-2026.md](../backfill-2024-2026.md).

## Décision
- **Le journal de bord devient une source à part entière**, `sos-logbook`, à côté du tableur. `catalog/logbook.py` (bibliothèque standard seule) lit le sitemap des rotations, chaque page du journal et la page d'archive, poliment : une requête par seconde, un agent identifié, ce que le `robots.txt` permet. Il produit une ligne par sauvetage terminé par l'Ocean Viking, dans l'ordre exact des colonnes du tableur, seulement après la dernière date du tableur.
- **Lecture planifiée** : `manage.py sync_logbook [--every N]` met les lignes en attente privée par `stage_snapshot`, comme un export du tableur, et note chaque lecture dans `SheetSync`. Un contenu identique est « inchangé » ; un site injoignable est « échec » sans arrêter la boucle.
- **Preuve gardée avec chaque ligne** : `LogbookEvidence` (page, rotation, heure de l'entrée, citation, points à vérifier). La fiche de l'espace équipe montre la phrase exacte du journal et le lien vers la page, à la place du numéro de ligne d'un tableur.
- **Vérification humaine inchangée** : les lignes passent par le même écran « Vérifier » que le tableur. Rien n'est relié, préparé ni publié automatiquement ; la source est créée sans accord de publication.
- **Sortie utile à SOS sans rien reconstruire** : `GET /api/private/v1/logbook/` dit l'écart (dernière date du tableur, lignes retrouvées, vérifiées, à vérifier) ; `GET /api/private/v1/logbook/export/` donne les lignes vérifiées en CSV, dans les colonnes du tableur, prêtes à y être collées. Avec l'accord de l'association, la carte existante les affiche alors.
- **Espace équipe** : une carte « Remettre la carte de SOS à jour » sur la page des données (le problème en une phrase, trois étapes, voir sur la carte, télécharger) ; un filtre « Retrouvé dans le journal de bord ». La vue mois par mois s'appelle désormais « Par mois », pour ne pas se confondre avec le journal de bord de SOS.

## Pourquoi pas autre chose
- Reconstruire une carte publique doublerait celle de CartONG, qui marche.
- Écrire directement dans le tableur Google demanderait un accès en écriture et l'accord de SOS ; l'export CSV laisse la décision à l'association.
- L'API WordPress de sosmediterranee.org est fermée (401) ; le sitemap et les pages HTML sont publics.

## Limites
- La lecture repose sur des formulations : 37 rotations sur 40 retombent exactement sur le total annoncé par SOS, 24 lignes portent une note à vérifier, trois cas n'ont pas de chiffre exploitable (81 personnes). Un changement de mise en page du site peut casser la lecture : il serait vu comme une lecture vide ou en échec, jamais comme des données inventées.
- Les sorties connues seulement par le site français (mai, septembre et octobre 2026) ne sont pas encore importées automatiquement ; le script les liste.
- Les notes « à vérifier » sont en anglais, comme le journal.
- Le site de SOS n'affiche aucune licence : les faits (dates, nombres) sont repris avec leur source, rien n'est publié sans l'accord de l'association.
