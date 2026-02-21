"""View mixins and classes for Table."""

import json
from collections.abc import Generator
from typing import Any

from datastar_py.django import (
    DatastarResponse,
    ServerSentEventGenerator,
)
from datastar_py.sse import DatastarEvent
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import render_to_string

from .config import (
    ACTION_PARAM,
    ACTION_SUBMIT_PARAM,
    COLUMN_SELECTION_PARAM,
    COLUMN_SELECTION_SUBMIT,
    PER_PAGE_SUBMIT_PARAM,
    PER_PAGE_VALUE_PARAM,
    PROFILE_ACTION_PARAM,
    PROFILE_ID_PARAM,
    PROFILE_NAME_PARAM,
    SELECTION_PARAM,
)


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

    # Handle POST actions (before any rendering)
    if request.method == "POST" and getattr(table, "actions", None):
        # 1) Regular form POST — action execution (Go button)
        #    Not a Datastar request; browser sends full form with checkboxes.
        if (
            ACTION_SUBMIT_PARAM in request.POST
            and request.headers.get("Datastar-Request") != "true"
        ):
            action_name = request.POST.get(ACTION_PARAM, "")
            selected = request.POST.getlist(SELECTION_PARAM)

            for action in table.actions:
                if action.name == action_name:
                    if action.requires_selection and not selected:
                        table.empty_selection_message = (
                            "No rows selected. Select at least one row first."
                        )
                        break  # fall through to render with message
                    # Guard: block confirmed (destructive) actions on all visible rows
                    if (
                        getattr(action, "confirm", None)
                        and selected
                    ):
                        visible_ids = json.loads(table.visible_ids_json)
                        if visible_ids and set(selected) >= set(visible_ids):
                            table.empty_selection_message = (
                                "Bulk operation on all visible rows is not"
                                " allowed. Select specific rows instead."
                            )
                            break  # fall through to render with message
                    result = action.handler(request, table, selected)
                    if isinstance(result, HttpResponse):
                        return result  # file download
                    return HttpResponseRedirect(request.get_full_path())  # PRG

            if not getattr(table, "empty_selection_message", None):
                return HttpResponseRedirect(request.get_full_path())

    if request.headers.get("Datastar-Request") == "true":
        # Pass all params to template (includes filterset, filter_fields, etc.)
        table_html = render_to_string(table._meta.template_name, params, request)

        # Build URL with current page number (preserves filter params from request.GET)
        query_params = request.GET.copy()
        page = getattr(table, "page", None)
        if page is not None:
            query_params["page"] = page.number
        query_params.pop("datastar", None)
        query_params.pop(COLUMN_SELECTION_PARAM, None)
        query_params.pop(COLUMN_SELECTION_SUBMIT, None)
        query_params.pop(PROFILE_ACTION_PARAM, None)
        query_params.pop(PROFILE_ID_PARAM, None)
        query_params.pop(PROFILE_NAME_PARAM, None)
        query_params.pop(PER_PAGE_SUBMIT_PARAM, None)
        query_params.pop(PER_PAGE_VALUE_PARAM, None)
        query_params.pop(ACTION_SUBMIT_PARAM, None)
        query_params.pop(ACTION_PARAM, None)
        query_params.pop(SELECTION_PARAM, None)
        current_url = f"{request.path}?{query_params.urlencode()}"

        # Update browser URL with current page number using History API
        js = f"history.replaceState(null, '', '{current_url}');"

        def table_updates() -> Generator[DatastarEvent, None, None]:
            yield ServerSentEventGenerator.execute_script(js)
            # Clear selection BEFORE morphing so new elements see cleared signals
            if (
                getattr(table, "actions", ())
                and table.table_name
                and not getattr(table.Meta, "infinite_scroll", False)
            ):
                select_all_signal = f"table{table.table_name}SelectAll"
                error_signal = f"table{table.table_name}Error"
                yield ServerSentEventGenerator.patch_signals(
                    {select_all_signal: False, error_signal: ""}
                )
            yield ServerSentEventGenerator.patch_elements(table_html)

        return DatastarResponse(table_updates())
    else:
        return render(request, template, params)
