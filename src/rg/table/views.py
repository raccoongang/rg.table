"""View mixins and classes for Table."""

import base64
import json
from collections.abc import Generator
from typing import Any

from datastar_py.django import (
    DatastarResponse,
    ServerSentEventGenerator,
)
from datastar_py.sse import DatastarEvent
from django.core.paginator import EmptyPage
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, QueryDict
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.translation import gettext, ngettext

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

CONFIRMED_PARAM = "_confirmed"


def _repaginate(table: Any) -> None:
    """Re-paginate to pick up data changes (e.g. after row deletion).

    After ``_build_visible_ids`` iterates ``table.paginated_rows`` during
    ``RequestConfig.configure()``, the page queryset is cached.  Calling
    ``table.paginate()`` again creates a fresh ``Paginator`` + ``Page``
    so the template sees the current DB state.
    """
    if not hasattr(table, "paginator"):
        return
    per_page = table.paginator.per_page
    page_number = table.page.number
    try:
        table.paginate(per_page=per_page, page=page_number)
    except EmptyPage:
        # Current page is now beyond last page — show last available page
        num_pages = table.paginator.num_pages
        table.page = table.paginator.page(max(num_pages, 1))


def _parse_datastar_filter_signals(
    request: HttpRequest, filter_names: set[str]
) -> dict[str, str]:
    """Extract validated filter params from the ``datastar`` query signal.

    Parses the JSON ``datastar`` query-string parameter sent by Datastar
    ``@get`` requests.  Only keys that appear in *filter_names* are kept,
    and only string values are accepted (no nested objects/arrays).

    Returns a dict of ``{param_name: value}`` ready to merge into a
    ``QueryDict``.
    """
    raw = request.GET.get("datastar")
    if not raw:
        return {}
    try:
        signals = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}
    if not isinstance(signals, dict):
        return {}
    result: dict[str, str] = {}
    for key, value in signals.items():
        if key not in filter_names:
            continue
        # Accept only scalar string values (or numbers cast to str)
        if isinstance(value, str):
            result[key] = value
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            result[key] = str(value)
    return result


def merge_datastar_filter_params(
    request: HttpRequest, filterset_class: type
) -> QueryDict:
    """Merge Datastar signal filter values into ``request.GET``.

    When a Datastar ``@get`` sends filter values as signals (inside the
    ``datastar`` JSON query parameter) rather than as top-level GET params,
    the Django filterset won't see them.  This helper promotes recognised
    filter params from the signal into a new ``QueryDict`` suitable for
    passing to a ``FilterSet`` constructor.

    Top-level GET params take precedence — signal values are only added
    for params not already present.

    Usage::

        data = merge_datastar_filter_params(request, MyFilterSet)
        filterset = MyFilterSet(data, queryset=qs)
    """
    filter_names = set(filterset_class.base_filters.keys())
    signal_params = _parse_datastar_filter_signals(request, filter_names)
    if not signal_params:
        return request.GET

    merged = request.GET.copy()
    for key, value in signal_params.items():
        if key not in merged:
            merged[key] = value
    return merged


def _get_template_kit(table: Any) -> str:
    """Extract template kit name from table's template_name."""
    # template_name is like "rg_table/bootstrap/table.html"
    parts: list[str] = table._meta.template_name.split("/")
    if len(parts) >= 2:
        return parts[-2]
    return "bootstrap"


def _clean_query_params(request: HttpRequest, table: Any) -> str:
    """Build clean URL with current page, stripping internal params.

    Filter values that arrived inside the ``datastar`` JSON signal are
    promoted to top-level query params so the URL is bookmarkable.
    """
    # Promote filter signals before stripping the datastar param
    filterset = getattr(table, "filterset", None)
    if filterset is not None:
        filter_names = set(filterset.filters.keys())
        signal_params = _parse_datastar_filter_signals(request, filter_names)
    else:
        signal_params = {}

    query_params = request.GET.copy()

    # Merge signal filter values (only if not already present as GET params)
    for key, value in signal_params.items():
        if key not in query_params:
            query_params[key] = value

    page = getattr(table, "page", None)
    if page is not None:
        query_params["page"] = page.number
    for param in (
        "datastar",
        COLUMN_SELECTION_PARAM,
        COLUMN_SELECTION_SUBMIT,
        PROFILE_ACTION_PARAM,
        PROFILE_ID_PARAM,
        PROFILE_NAME_PARAM,
        PER_PAGE_SUBMIT_PARAM,
        PER_PAGE_VALUE_PARAM,
        ACTION_SUBMIT_PARAM,
        ACTION_PARAM,
        SELECTION_PARAM,
    ):
        query_params.pop(param, None)
    return f"{request.path}?{query_params.urlencode()}"


def _table_sse_response(
    request: HttpRequest,
    table: Any,
    params: dict[str, Any],
) -> DatastarResponse:
    """Build a Datastar SSE response that re-renders the full table."""
    table_html = render_to_string(table._meta.template_name, params, request)
    current_url = _clean_query_params(request, table)
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
            yield ServerSentEventGenerator.patch_signals(
                {select_all_signal: False}
            )
        yield ServerSentEventGenerator.patch_elements(table_html)

    return DatastarResponse(table_updates())


def _action_error_sse(
    request: HttpRequest, table: Any, message: str
) -> DatastarResponse:
    """Return SSE that morphs error message into the action bar."""
    table.empty_selection_message = message
    kit = _get_template_kit(table)
    html = render_to_string(
        f"rg_table/{kit}/action_bar.html",
        {"table": table, "request": request},
        request,
    )

    def events() -> Generator[DatastarEvent, None, None]:
        yield ServerSentEventGenerator.patch_elements(html)

    return DatastarResponse(events())


def _action_confirm_sse(
    request: HttpRequest,
    table: Any,
    action: Any,
    selected: list[str],
    *,
    confirm_message: str | None = None,
) -> DatastarResponse:
    """Return SSE that morphs confirmation UI into the action bar."""
    kit = _get_template_kit(table)
    html = render_to_string(
        f"rg_table/{kit}/action_confirm.html",
        {
            "table_name": table.table_name,
            "action_name": action.name,
            "confirm_message": confirm_message or action.confirm,
            "selected": selected,
            "url": request.get_full_path(),
        },
        request,
    )

    def events() -> Generator[DatastarEvent, None, None]:
        yield ServerSentEventGenerator.patch_elements(html)

    return DatastarResponse(events())


def _action_download_sse(
    response: HttpResponse, table: Any
) -> DatastarResponse:
    """Return SSE that triggers a browser download via blob URL."""
    content_b64 = base64.b64encode(response.content).decode()
    content_type = response["Content-Type"].split(";")[0]

    # Extract filename from Content-Disposition header
    disposition = response.get("Content-Disposition", "")
    filename = "download"
    if 'filename="' in disposition:
        filename = disposition.split('filename="')[1].split('"')[0]
    elif "filename=" in disposition:
        filename = disposition.split("filename=")[1].split(";")[0].strip()
    filename = filename.replace("\\", "\\\\").replace("'", "\\'")

    select_all_signal = f"table{table.table_name}SelectAll"
    busy_signal = f"table{table.table_name}ActionBusy"
    js = (
        f"var b=atob('{content_b64}'),"
        f"a=new Uint8Array(b.length),i=0;"
        f"for(;i<b.length;i++)a[i]=b.charCodeAt(i);"
        f"var u=URL.createObjectURL(new Blob([a],"
        f"{{type:'{content_type}'}})),"
        f"l=document.createElement('a');"
        f"l.href=u;l.download='{filename}';l.click();"
        f"URL.revokeObjectURL(u);"
    )

    def events() -> Generator[DatastarEvent, None, None]:
        yield ServerSentEventGenerator.execute_script(js)
        yield ServerSentEventGenerator.patch_signals(
            {select_all_signal: False, busy_signal: False}
        )

    return DatastarResponse(events())


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
    is_datastar = request.headers.get("Datastar-Request") == "true"

    # Handle POST actions (before any rendering)
    if request.method == "POST" and getattr(table, "actions", None):
        if ACTION_SUBMIT_PARAM in request.POST:
            action_name = request.POST.get(ACTION_PARAM, "")
            selected = request.POST.getlist(SELECTION_PARAM)

            for action in table.actions:
                if action.name == action_name:
                    # Confirmation check (Datastar only, not yet confirmed)
                    if (
                        action.confirm
                        and CONFIRMED_PARAM not in request.POST
                    ):
                        if is_datastar:
                            if not selected:
                                # No selection → whole dataset
                                total = (
                                    table.paginator.count
                                    if hasattr(table, "paginator")
                                    else len(table.data)
                                )
                                msg = (
                                    gettext(
                                        "This will affect all"
                                        " %(total)s records."
                                    )
                                    % {"total": total}
                                    + " "
                                    + action.confirm
                                )
                            else:
                                count = len(selected)
                                msg = (
                                    ngettext(
                                        "%(count)s record selected.",
                                        "%(count)s records selected.",
                                        count,
                                    )
                                    % {"count": count}
                                    + " "
                                    + action.confirm
                                )
                            return _action_confirm_sse(
                                request, table, action, selected,
                                confirm_message=msg,
                            )
                        # Non-Datastar: execute anyway (no confirm w/o JS)

                    # Execute action
                    result = action.handler(request, table, selected)
                    if isinstance(result, HttpResponse):
                        if is_datastar:
                            return _action_download_sse(result, table)
                        return result  # file download
                    if is_datastar:
                        # Re-paginate so the template sees fresh DB state
                        _repaginate(table)
                        return _table_sse_response(request, table, params)
                    return HttpResponseRedirect(
                        request.get_full_path()
                    )  # PRG

            if not getattr(table, "empty_selection_message", None):
                if is_datastar:
                    return _table_sse_response(request, table, params)
                return HttpResponseRedirect(request.get_full_path())

    if is_datastar:
        return _table_sse_response(request, table, params)
    else:
        return render(request, template, params)
