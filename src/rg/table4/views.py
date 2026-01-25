"""View mixins and classes for Table4."""

from django.views.generic import ListView

from django_tables2 import SingleTableMixin

from .tables import Table4
from django.shortcuts import render
from django.template.loader import render_to_string

from datastar_py.django import (
    DatastarResponse,
    ServerSentEventGenerator,
    read_signals,
)



def table_render(request, template, params):
    """
    Conditionally render table for Datastar request or the whole page, depending
    on request.
    """
    table = params['table']
    if request.headers.get('Datastar-Request') == 'true':
        table_html = render_to_string(table._meta.template_name, {"table": table}, request)
        def table_updates():
            yield ServerSentEventGenerator.patch_elements(table_html)
        return DatastarResponse(table_updates())
    else:
        return render(request, template, {
            "table": table,
            "table_variant": "Plain Table",
        })


class Table4Mixin(SingleTableMixin):
    """
    Mixin for adding Table4 support to any class-based view.

    Example:
        class MyView(Table4Mixin, ListView):
            model = MyModel
            table_class = MyTable
    """

    table_class: type[Table4] | None = None


class Table4ListView(Table4Mixin, ListView):
    """
    ListView with Table4 support.

    Example:
        class MyListView(Table4ListView):
            model = MyModel
            table_class = MyTable
            paginate_by = 25
    """

    pass
