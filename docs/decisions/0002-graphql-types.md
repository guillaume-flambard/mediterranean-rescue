# ADR 0002 : GraphQL et types backend/frontend

**Statut : remplacé par [ADR 0003 REST/OpenAPI](0003-rest-openapi.md), sur décision de Guillaume le 24 octobre 2026. Document historique, non applicable au code actif.**

Décision historique : GraphQL pour les lectures applicatives, Strawberry Django côté serveur, urql et GraphQL Code Generator côté React. Demandé et retenu le 24 octobre 2026. REST n’est plus le contrat retenu ; health/CSRF et l’administration restent des routes HTTP ordinaires.

Django conserve le modèle de données, les migrations, les contraintes SQL, les sessions et permissions. Strawberry déclare explicitement les champs publics, avec une intégration ORM. Nous ne générons pas une API publique de tous les modèles et ne publions pas les champs internes.

Chaîne vérifiable :

```text
Modèles et types Python Strawberry
    → export Django de contracts/schema.graphql
    → validation des opérations frontend/*.graphql
    → génération des TypedDocumentNode (résultats et variables)
    → urql useQuery(document, variables)
    → TypeScript strict et build
```

Une requête ne reçoit que le type des champs qu’elle sélectionne, pas un objet Event géant supposé complet. Date et UUID sont mappés explicitement à string. Les coordonnées ont un objet typé Position, pas un scalar JSON sans contrat. Les inconnus métier restent nullable ; TypeScript impose leur prise en compte. strictScalars fait échouer la génération si un nouveau scalar apparaît sans mapping.

La CI réexporte le schéma depuis le backend, régénère le client et refuse une différence non commitée. Elle vérifie aussi qu’une requête volontairement invalide est rejetée. Cela attrape suppression/renommage d’un champ, argument invalide, enum inconnu, changement de nullabilité et types de variables incohérents.

Les limites : un string Date TypeScript n’est pas une validation calendaire, les données externes peuvent être fausses malgré des types corrects, et un client qui contourne notre frontend existe toujours. Le serveur valide donc dates, coordonnées, effectifs, permissions, publication et pagination à l’exécution. Les données Sheets passent par des parseurs puis des règles métier avant PostGIS. Les erreurs GraphQL et états partiels doivent être traités par l’UI.

Coûts assumés : génération dans le workflow de contribution, contrôle des requêtes coûteuses, permissions par accès et tests contre N+1. Limites de profondeur, alias, pagination et taille de requête ; aucun write anonyme. Pas de subscriptions, fédération ou gateway dans cette tranche. Les mutations futures utiliseront les services transactionnels de domaine existants.

Sources : https://strawberry.rocks/docs/django ; https://strawberry.rocks/docs/django/guide/export-schema ; https://the-guild.dev/graphql/codegen/plugins/presets/preset-client ; https://strawberry.rocks/docs/extensions/query-depth-limiter ; https://strawberry.rocks/docs/extensions/max-aliases-limiter.
