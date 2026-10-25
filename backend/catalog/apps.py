from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CatalogConfig(AppConfig):
    name = "catalog"
    verbose_name = _("Data and publication")
    default_auto_field = "django.db.models.BigAutoField"
