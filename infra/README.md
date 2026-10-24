# Exécution et exploitation

Compose sert au développement local et à la CI. Le backend WSGI Gunicorn utilise deux processus sans threads pour GeoDjango. Le frontend est un build statique Vite. La production devra avoir un proxy même origine : / vers frontend/dist, /api/ vers Django, /admin/ vers administration protégée, /static/ vers collectstatic. Pas de CORS global permissif. La session et CSRF restent vérifiés côté Django ; les endpoints REST publics de lecture n’exigent pas de token CSRF.

La configuration production échoue sans un secret long. DEBUG est false par défaut en production, HTTPS/cookies sécurisés/HSTS sont activés. Les paramètres de proxy et domaines doivent être décidés au déploiement, pas remplacés par des wildcards. Le rôle PostgreSQL runtime ne sera pas superuser ni CREATEDB ; le compte de migration distinct possédera uniquement les droits nécessaires. Le rôle local rescue a CREATEDB uniquement pour créer la base de test.

Pour que l’administration soit utilisable en développement, lancer le backend de développement via la commande Compose documentée (runserver sert les static admin en DEBUG), ou utiliser un proxy local de static. Gunicorn ne sert pas automatiquement ces fichiers. Aucun compte administrateur par défaut n’est créé.

Migrations : 0001 crée le schéma neuf, sans modification d’une base métier externe. Rollback local sur une base dédiée sans données à conserver : migrate catalog zero, puis migrate catalog. Une base avec imports exige sauvegarde et plan de conservation avant toute inversion : retirer des tables est destructeur. Aucun rollback de données réelles exécuté ici.

Sauvegarde avant mise en production : pg_dump format custom, copie chiffrée hors hôte, rétention approuvée et test de restauration dans une base dédiée. Objectifs proposés RPO24h/RTO4h, à valider. Le pipeline d’import conserve checksum et statut ; son erreur doit être observable sans exposer de payload dans les logs publics. Pas de tâches réseau autonomes dans cette tranche.

Démarrage : initialisation des secrets → DB healthy → migrate explicite → API. L’API ne lance pas de migration automatiquement au démarrage d’un worker. Health /api/health/ renvoie 503 si la DB est indisponible. Ne pas lancer docker compose down -v pour dépanner : les volumes portent l’historique.
