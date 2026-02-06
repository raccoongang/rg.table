"""Django app configuration."""

from django.apps import AppConfig


class TableConfig(AppConfig):
    """Configuration for rg.table app."""

    name = "rg.table"
    label = "rg_table"
    verbose_name = "RG Table"
    default_auto_field = "django.db.models.BigAutoField"
