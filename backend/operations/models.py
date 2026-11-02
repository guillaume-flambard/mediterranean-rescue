# Les modèles décrivent les tables de la base de données : chaque classe devient une table,
# chaque attribut une colonne. Il n'y en a pas encore : le premier, Operation, est une issue.
# Après toute modification de ce fichier :
#   uv run manage.py makemigrations operations   (écrit la migration, à committer)
#   uv run manage.py migrate                     (l'applique à ta base)
# Voir le tutoriel, partie 2 : https://docs.djangoproject.com/fr/6.1/intro/tutorial02/
