"""Database models for rg.table."""

from django.conf import settings
from django.db import models


class TableProfile(models.Model):
    """A named set of table preferences (columns, per_page, sort) for a user."""

    objects: models.Manager["TableProfile"] = models.Manager()

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="table_profiles",
    )
    table_name = models.CharField(max_length=255, db_index=True)
    name = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)

    # Preferences
    columns = models.JSONField(default=list, blank=True)
    per_page = models.PositiveIntegerField(null=True, blank=True)
    sort_order = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "table_name", "name"],
                name="unique_user_table_profile",
            ),
        ]
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.table_name})"
