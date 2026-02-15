"""Views for geodata app."""

from django.shortcuts import redirect, render

from rg.table import RequestConfig, table_render

from .filters import GeoNameFilterSet
from .models import GeoName
from .tables import (
    GeoNameFilteredTable,
    GeoNameInfiniteTable,
    GeoNamePlainTable,
    GeoNameSortableTable,
)


def index_redirect(request):
    """Redirect to default kit index."""
    return redirect("geodata:index-bootstrap")


# Bootstrap views

def index_bootstrap(request):
    """Index page for Bootstrap kit."""
    return render(request, "geodata/index2_bootstrap.html", {"current_kit": "bootstrap"})


def plain_table_bootstrap(request):
    """Plain table with Bootstrap."""
    queryset = GeoName.objects.all()
    table = GeoNamePlainTable(queryset, template_kit="bootstrap", name='plain')
    RequestConfig(request, paginate={"per_page": 15}).configure(table)
    return table_render(request, "geodata/geoname_list_bootstrap.html", {
        "table": table,
        "table_variant": "Plain Table",
    })


def sortable_table_bootstrap(request):
    """Sortable table with Bootstrap."""
    queryset = GeoName.objects.all()
    table = GeoNameSortableTable(queryset, template_kit="bootstrap")
    RequestConfig(request, paginate={"per_page": 15}).configure(table)
    return render(request, "geodata/geoname_list_bootstrap.html", {
        "table": table,
        "table_variant": "Sortable Table",
    })


def filtered_table_bootstrap(request):
    """Filtered table with Bootstrap."""
    queryset = GeoName.objects.all()
    filterset = GeoNameFilterSet(request.GET, queryset=queryset)

    table = GeoNameFilteredTable(
        filterset.qs,
        template_kit="bootstrap",
        template_name="rg_table/bootstrap/table_filtered.html",
        name="filtered",
    )
    table.filterset = filterset
    # Attach filter_fields to table for template access via {% render_table %}
    table.filter_fields = [
        (name, filterset.form[name])
        for name in filterset.filters.keys()
        if name != "q"
    ]

    RequestConfig(request, paginate={"per_page": 15}).configure(table)

    return table_render(request, "geodata/geoname_list_bootstrap.html", {
        "table": table,
        "table_variant": "Filtered Table",
    })


def infinite_table_bootstrap(request):
    """Infinite scroll table with Bootstrap."""
    queryset = GeoName.objects.all()
    per_page = min(int(request.GET.get('per_page', 15)), 500)  # Cap at 500

    table = GeoNameInfiniteTable(
        queryset,
        template_kit="bootstrap",
        template_name="rg_table/bootstrap/table_infinite.html",
        name="infinite",
    )

    RequestConfig(request, paginate={"per_page": per_page}).configure(table)

    return table_render(request, "geodata/geoname_list_bootstrap.html", {
        "table": table,
        "table_variant": "Infinite Scroll",
    })


def column_select_table_bootstrap(request):
    """Column selection table with Bootstrap."""
    queryset = GeoName.objects.all()
    table = GeoNameSortableTable(
        queryset,
        template_kit="bootstrap",
        name="colselect",
        enable_column_selection=True,
    )
    RequestConfig(request, paginate={"per_page": 15}).configure(table)
    return table_render(request, "geodata/geoname_list_bootstrap.html", {
        "table": table,
        "table_variant": "Column Selection",
    })


# Bulma views

def index_bulma(request):
    """Index page for Bulma kit."""
    return render(request, "geodata/index2_bulma.html", {"current_kit": "bulma"})


def plain_table_bulma(request):
    """Plain table with Bulma."""
    queryset = GeoName.objects.all()
    table = GeoNamePlainTable(queryset, template_kit="bulma")
    RequestConfig(request, paginate={"per_page": 15}).configure(table)
    return render(request, "geodata/geoname_list_bulma.html", {
        "table": table,
        "table_variant": "Plain Table",
    })


def sortable_table_bulma(request):
    """Sortable table with Bulma."""
    queryset = GeoName.objects.all()
    table = GeoNameSortableTable(queryset, template_kit="bulma")
    RequestConfig(request, paginate={"per_page": 15}).configure(table)
    return render(request, "geodata/geoname_list_bulma.html", {
        "table": table,
        "table_variant": "Sortable Table",
    })


def filtered_table_bulma(request):
    """Filtered table with Bulma."""
    queryset = GeoName.objects.all()
    filterset = GeoNameFilterSet(request.GET, queryset=queryset)

    table = GeoNameFilteredTable(
        filterset.qs,
        template_kit="bulma",
        template_name="rg_table/bulma/table_filtered.html",
        name="filtered",
    )
    table.filterset = filterset
    # Attach filter_fields to table for template access via {% render_table %}
    table.filter_fields = [
        (name, filterset.form[name])
        for name in filterset.filters.keys()
        if name != "q"
    ]

    RequestConfig(request, paginate={"per_page": 15}).configure(table)

    return table_render(request, "geodata/geoname_list_bulma.html", {
        "table": table,
        "table_variant": "Filtered Table",
    })


def infinite_table_bulma(request):
    """Infinite scroll table with Bulma."""
    queryset = GeoName.objects.all()
    per_page = min(int(request.GET.get('per_page', 15)), 500)  # Cap at 500

    table = GeoNameInfiniteTable(
        queryset,
        template_kit="bulma",
        template_name="rg_table/bulma/table_infinite.html",
        name="infinite",
    )

    RequestConfig(request, paginate={"per_page": per_page}).configure(table)

    return table_render(request, "geodata/geoname_list_bulma.html", {
        "table": table,
        "table_variant": "Infinite Scroll",
    })


def column_select_table_bulma(request):
    """Column selection table with Bulma."""
    queryset = GeoName.objects.all()
    table = GeoNameSortableTable(
        queryset,
        template_kit="bulma",
        name="colselect",
        enable_column_selection=True,
    )
    RequestConfig(request, paginate={"per_page": 15}).configure(table)
    return table_render(request, "geodata/geoname_list_bulma.html", {
        "table": table,
        "table_variant": "Column Selection",
    })
