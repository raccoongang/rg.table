"""GeoNames data model."""

from django.db import models


class GeoName(models.Model):
    """
    GeoNames geographical data.

    Data source: https://download.geonames.org/export/dump/
    License: Creative Commons Attribution 4.0
    """

    geonameid = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200, db_index=True)
    asciiname = models.CharField(max_length=200, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    feature_class = models.CharField(max_length=1, db_index=True)
    feature_code = models.CharField(max_length=10, db_index=True)
    country_code = models.CharField(max_length=2, db_index=True)
    admin1_code = models.CharField(max_length=20, blank=True)
    population = models.BigIntegerField(default=0, db_index=True)
    elevation = models.IntegerField(null=True, blank=True)
    timezone = models.CharField(max_length=40, blank=True)
    modification_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-population"]
        indexes = [
            # Composite indexes for filtering + ordering by population (descending)
            models.Index(fields=["country_code", "-population"]),
            models.Index(fields=["feature_class", "-population"]),
            # For combined country + feature filtering
            models.Index(fields=["country_code", "feature_class", "-population"]),
            # For search + ordering (helps with prefix searches)
            models.Index(fields=["name", "-population"]),
            # For asciiname search
            models.Index(fields=["asciiname"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.country_code})"
