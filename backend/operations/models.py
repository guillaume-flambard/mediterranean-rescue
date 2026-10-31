# Les modèles décrivent les tables de la base de données. Chaque classe devient une table,
# chaque attribut une colonne. Après toute modification de ce fichier :
#   uv run manage.py makemigrations operations   (écrit la migration)
#   uv run manage.py migrate                     (l'applique à la base)
# Voir le tutoriel, partie 2 : https://docs.djangoproject.com/fr/6.1/intro/tutorial02/

from django.db import models


class Operation(models.Model):
    """Une opération en mer : sauvetage, transfert, évacuation médicale..."""

    # Les types possibles. La valeur de gauche est stockée en base (en anglais, comme le
    # code) ; le libellé de droite est affiché dans l'admin.
    class Kind(models.TextChoices):
        RESCUE = "rescue", "Sauvetage"
        TRANSFER = "transfer", "Transfert"
        MEDEVAC = "medevac", "Évacuation médicale"
        INCIDENT = "incident", "Incident"
        SHIPWRECK = "shipwreck", "Naufrage"
        DEAD_MISSING = "dead_missing", "Morts et disparus"

    # Le premier argument de chaque champ est son libellé dans l'admin.
    kind = models.CharField("type", max_length=20, choices=Kind)
    occurred_on = models.DateField("date")
    title = models.CharField("titre", max_length=240)
    summary = models.TextField("résumé", blank=True)

    # Règle du projet : une valeur inconnue reste vide, jamais zéro.
    # null=True autorise le vide en base, blank=True l'autorise dans les formulaires.
    people = models.PositiveIntegerField(
        "personnes", null=True, blank=True, help_text="Laisser vide si le nombre est inconnu."
    )
    # Position en degrés (WGS84, comme un GPS). Vide si la position est inconnue :
    # l'opération n'a alors pas de point sur la carte.
    latitude = models.FloatField("latitude", null=True, blank=True)
    longitude = models.FloatField("longitude", null=True, blank=True)

    # D'où vient l'information : chaque opération affichée doit avoir une source.
    source_url = models.URLField("adresse de la source", max_length=1000)

    # Rien n'est public tant qu'une personne n'a pas vérifié la source et coché cette case.
    published = models.BooleanField(
        "publiée", default=False, help_text="Cocher seulement après avoir vérifié la source."
    )

    class Meta:
        verbose_name = "opération"
        verbose_name_plural = "opérations"
        # Les plus récentes d'abord.
        ordering = ["-occurred_on"]

    def __str__(self):
        # Le texte qui représente une opération dans l'admin (tutoriel, partie 2).
        return self.title
