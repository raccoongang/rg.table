"""FilterSet definitions for geodata app."""

import django_filters

from .models import GeoName


class GeoNameFilterSet(django_filters.FilterSet):
    """FilterSet for GeoName model with search and dropdown filters."""

    q = django_filters.CharFilter(
        method="filter_search",
        label="Search",
    )

    country_code = django_filters.ChoiceFilter(
        choices=[],  # Populated dynamically
        empty_label="All Countries",
    )

    feature_class = django_filters.ChoiceFilter(
        choices=[],  # Populated dynamically
        empty_label="All Types",
    )

    class Meta:
        model = GeoName
        fields = ["country_code", "feature_class"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate choices dynamically from database
        self.filters["country_code"].extra["choices"] = (
            GeoName.objects.values_list("country_code", "country_code")
            .distinct()
            .order_by("country_code")
        )
        self.filters["feature_class"].extra["choices"] = (
            GeoName.objects.values_list("feature_class", "feature_class")
            .distinct()
            .order_by("feature_class")
        )

    def filter_search(self, queryset, name, value):
        """Search across name field."""
        if value:
            return queryset.filter(name__icontains=value)
        return queryset
