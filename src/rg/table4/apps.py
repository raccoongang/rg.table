"""Django app configuration."""

from django.apps import AppConfig


class Table4Config(AppConfig):
    """Configuration for rg.table4 app."""

    name = "rg.table4"
    label = "rg_table4"
    verbose_name = "RG Table4"
    default_auto_field = "django.db.models.BigAutoField"
