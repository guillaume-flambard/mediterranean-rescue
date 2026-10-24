# Exigences fondation
REQ-F1 architecture et inventaire sourcés ; REQ-F2 modèles PostGIS et migrations réversibles ; REQ-F3 API REST publique filtrée et bornée, aucun staging exposé ; REQ-F4 types générés backend/frontend et contrôle CI ; REQ-F5 frontend React/Base UI/MapLibre connecté, loading/empty/error ; REQ-F6 import local atomique, provenance, idempotence et publication autorisée/auditée ; REQ-F7 exécution reproductible, secrets hors Git, tests DB réelle et documentation.
Schéma et limites détaillés docs/architecture.md. L’API initiale est en lecture seule ; édition par administration Django, aucun upload anonyme. Champs absents null, sources non autorisées privées. Pas de migration destructive d’une base existante : nouvelle base dédiée.

Contrat révisé : docs/decisions/0003-rest-openapi.md. Les exigences R-REST-1..4 et R-DOC-1 remplacent les critères de transport GraphQL historiques ; les invariants métier F2/F6 sont conservés. Document de départ : docs/PROJECT.md.
