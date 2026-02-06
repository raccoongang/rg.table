"""View mixins and classes for Table."""

from collections.abc import Generator
from typing import Any

from datastar_py.django import (
    DatastarResponse,
    ServerSentEventGenerator,
)
from datastar_py.sse import DatastarEvent
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string


def table_render(
    request: HttpRequest,
    template: str,
    params: dict[str, Any],
) -> HttpResponse | DatastarResponse:
    """
    Conditionally render table for Datastar request or the whole page, depending
    on request.
    """
    table = params["table"]
    if request.headers.get("Datastar-Request") == "true":
        # Pass all params to template (includes filterset, filter_fields, etc.)
        table_html = render_to_string(table._meta.template_name, params, request)

        # Build URL with current page number (preserves filter params from request.GET)
        query_params = request.GET.copy()
        query_params["page"] = table.page.number
        query_params.pop("datastar", None)
        current_url = f"{request.path}?{query_params.urlencode()}"

        # Update browser URL with current page number using History API
        js = f"history.replaceState(null, '', '{current_url}');"

        def table_updates() -> Generator[DatastarEvent, None, None]:
            yield ServerSentEventGenerator.execute_script(js)
            yield ServerSentEventGenerator.patch_elements(table_html)

        return DatastarResponse(table_updates())
    else:
        return render(request, template, params)
