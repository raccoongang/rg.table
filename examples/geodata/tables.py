"""Table definitions for geodata app."""

import django_tables2 as tables

from rg.table import Table, TableMeta

from .filters import GeoNameFilterSet
from .models import GeoName


class GeoNameTableBase(Table):
    """Base table for GeoNames data with common column definitions."""

    name = tables.Column(linkify=False)
    country_code = tables.Column(verbose_name="Country")
    population = tables.Column()
    latitude = tables.Column()
    longitude = tables.Column()
    feature_class = tables.Column(verbose_name="Type")
    timezone = tables.Column()

    class Meta(TableMeta):
        model = GeoName
        fields = (
            "name",
            "country_code",
            "population",
            "latitude",
            "longitude",
            "feature_class",
            "timezone",
        )


class GeoNamePlainTable(GeoNameTableBase):
    """Plain table with no sorting."""

    class Meta(GeoNameTableBase.Meta):
        orderable = False


class GeoNameSortableTable(GeoNameTableBase):
    """Table with sorting enabled."""

    class Meta(GeoNameTableBase.Meta):
        orderable = True


class GeoNameFilteredTable(GeoNameTableBase):
    """Table with filters enabled."""

    class Meta(GeoNameTableBase.Meta):
        orderable = True
        filterset_class = GeoNameFilterSet


class GeoNameInfiniteTable(GeoNameTableBase):
    """Table with infinite scroll enabled."""

    class Meta(GeoNameTableBase.Meta):
        orderable = True
        infinite_scroll = True


class GeoNameProfileTable(GeoNameTableBase):
    """Table with profiles, column selection, and per-page selection enabled."""

    class Meta(GeoNameTableBase.Meta):
        orderable = True
        enable_column_selection = True
        enable_profiles = True
        enable_per_page_selection = True
        per_page_choices = (10, 15, 25, 50)
        pinned_columns = ("name",)


# Alias for backwards compatibility
GeoNameTable = GeoNamePlainTable
