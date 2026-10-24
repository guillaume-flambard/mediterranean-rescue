# ADR 0009 : API privée de revue (UI1)

Statut : accepté par Guillaume le 24 octobre 2026 (« d'abord le contrat des API privées de revue : sessions, CSRF, permissions, erreurs »). Dépend des ADR 0003, 0005 et 0008, et des parcours W04 et W05 de `docs/design/user-flows.md`.

## Principes
- Préfixe `/api/private/v1/`, URL en anglais, distinct de l'API publique `/api/v1/` qui reste sans authentification et inchangée.
- **Session Django** : la connexion passe par la page de connexion existante (`/admin/login/`, compte `is_staff` pour l'instant) ; l'application redirige vers elle avec `next`. Aucun jeton dans le navigateur, aucun mot de passe géré par le frontend. Un écran de connexion dédié pourra venir plus tard sans changer ce contrat.
- **CSRF** : toute écriture exige l'en-tête `X-CSRFToken`. Le cookie CSRF reste `HttpOnly` ; le frontend lit le jeton sur `GET /api/csrf/` et le renvoie. Origines de confiance : `CSRF_TRUSTED_ORIGINS`.
- **Permissions** revérifiées côté serveur à chaque requête : utilisateur actif et `catalog.review_identity` pour toute la revue. Les services de l'ADR 0005 restent les seuls à écrire ; l'API ne réimplémente aucune règle.
- **Données privées** : réponses `Cache-Control: no-store` ; les URL ne portent que des identifiants opaques (UUID) et des critères sans valeur brute ; aucune donnée n'est conservée dans le stockage du navigateur.

## Erreurs
Même enveloppe que l'API publique, `{code, detail, errors?}`, avec des codes explicites pour l'API privée :

| Statut | Code | Sens pour l'interface |
| --- | --- | --- |
| 400 | `invalid` | Saisie à corriger, détail par champ dans `errors` |
| 401 | `not_authenticated` | Session absente ou expirée : se connecter puis relire l'état |
| 403 | `permission_denied` | Connecté mais sans le droit : le dire, sans masquer en « aucun résultat » |
| 403 | `csrf_failed` | Jeton absent ou périmé : le client relit le jeton et réessaie une fois |
| 404 | `not_found` | Identifiant inconnu |
| 405 | `method_not_allowed` | Méthode non prévue |
| 409 | `conflict` | L'état a changé (autre relecteur, ligne déjà liée, identité déjà utilisée) ou la règle métier refuse : relire puis redécider ; `detail` explique sans valeur brute |

## Ressources
- `GET me/` : nom d'utilisateur et droits utiles à l'interface (`review_identity`).
- `GET snapshots/?sheet=&limit=&offset=` : exports enregistrés (source, onglet, date, lignes, statut de lecture), les plus récents d'abord.
- `GET review/rows/?snapshot=<uuid>&status=to_review|blocked|linked&limit=&offset=` : file paginée (25 par défaut, 100 au plus) d'un export, avec les compteurs des trois facettes exclusives. `to_review` regroupe les propositions `new`, `exact_carry` et `candidates`.
- `GET review/rows/<uuid>/` : la ligne reçue (en-têtes et cellules brutes, provenance), son interprétation, ses erreurs, la proposition et ses candidats résumés, ou la décision déjà enregistrée.
- `POST review/rows/<uuid>/decision/` : `{action: "create_identity" | "link", identity: <uuid>?, reason}` ; appelle `approve_link`. Un choix manuel est enregistré `reviewed_match`.
- `POST review/snapshots/<uuid>/exact-carries/` : `{rows: [<uuid>…], reason}` ; seules les lignes sélectionnées et encore éligibles, revérifiées au serveur, en une transaction ; sinon `409` sans rien écrire.
- `GET review/identities/?snapshot=<uuid>&q=&limit=` : identités de la même source et du même onglet pour la recherche de rattachement ; `q` filtre sur la date (préfixe AAAA-MM-JJ) ou le début de l'identifiant.

« Examiner plus tard » n'appelle aucune API : rien n'est créé.

## Hors périmètre
Import et diagnostic HTTP (UI2), ports (UI2), brouillons et révisions (UI3), écran de connexion dédié, limitation de débit.
