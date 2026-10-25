# Architecture de Mediterranée Rescue

Architecture courante : REST, décision de Guillaume du 24 octobre 2026. Le [document de départ](PROJECT.md) contient le cadrage complet, le modèle, les invariants, la roadmap et les critères de sortie. [ADR 0003](decisions/0003-rest-openapi.md) définit le contrat et sa vérification ; ADR 0002 est remplacé. Les anciennes preuves GraphQL sont historiques.

## Modules et responsabilités

backend/catalog/models.py : persistance et contraintes PostGIS ; services.py : publication transactionnelle et audit ; imports.py : validation/staging/application atomique ; admin.py : administration avec permissions et gardes anti-modification indirecte ; api.py : projections publiques, filtres partagés et endpoints de lecture. backend/rescue porte configuration, middleware de limites et routes.

frontend/src/api/schema.d.ts est généré depuis contracts/openapi.yaml. client.ts branche le client typé sur les hooks TanStack Query. App.tsx porte filtres, liste, pagination, fiche et preuves paginées ; components/Map.tsx charge MapLibre et son worker local à la demande. Le fond Natural Earth est une ressource locale du domaine public.

## Choix techniques

React 19, TypeScript strict, Vite, Base UI 1.9, MapLibre 6 ; Django 5.2 LTS, Django REST Framework et drf-spectacular ; PostgreSQL 17/PostGIS 3.6. Versions effectives dans uv.lock et frontend/pnpm-lock.yaml. Monorepo et monolithe modulaire, pas de service distribué ajouté sans besoin mesuré.

## Frontières

Source autorisée → snapshot/adaptateur → staging privé → revue → brouillon → publication auditée → queryset public → sérialiseurs explicites → API REST → carte et liste. Seuls les événements publiés, avec droits/licence et bon mode réel/synthétique, sont visibles. La révocation est appliquée à chaque requête ; HTTP no-store. Pas de mutation anonyme, pas de téléchargement serveur d’URL arbitraire, sessions/CSRF pour l’admin.

Les relations ne doivent pas permettre de modifier indirectement un événement déjà publié. Les effectifs et positions inconnus restent null. Aucun numéro de ligne ne sert d’identité stable. Les données réelles SOS, leurs licences et le crosswalk ne sont pas encore intégrés.

## Contrat et vérification

/api/v1/events/, /api/v1/events/{id}/, /api/v1/events/{id}/evidence/, /api/v1/map-points/ et /api/v1/schema/. Les lectures liste/carte partagent les filtres ; pagination et plafond de points sont explicites. Les erreurs sont structurées code/detail/errors optionnel. Le JSON runtime est produit par des sérialiseurs testés ; les types frontend n’assurent pas la vérité des données.

La CI exécute tests PostGIS, absence de dérive de migration, contrôle Django production, export OpenAPI validé sans avertissement, génération TypeScript, refus de dérive, preuve négative de compilation, tests frontend et build. Développement Compose ; WSGI Gunicorn pour packaging ; frontend statique. Déploiement, rôles d’exploitation, TLS, sauvegardes hors machine et restauration testée restent requis avant lancement.

Références : [Django déploiement](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/), [DRF documentation API](https://www.django-rest-framework.org/topics/documenting-your-api/), [drf-spectacular](https://drf-spectacular.readthedocs.io/en/stable/), [OpenAPI client](https://openapi-ts.dev/openapi-react-query/), [Base UI](https://base-ui.com/react/overview/quick-start), [MapLibre](https://maplibre.org/maplibre-gl-js/docs/).
