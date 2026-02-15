from typing import Any

from django.core.paginator import EmptyPage, PageNotAnInteger
from django.http import HttpRequest

COLUMN_SELECTION_PARAM = "_columns"
COLUMN_SELECTION_SUBMIT = "_columns_submit"
SESSION_KEY_PREFIX = "rg_table:columns"


def _session_key(table_name: str) -> str:
    return f"{SESSION_KEY_PREFIX}:{table_name}"


def get_column_preference(session: Any, table_name: str) -> list[str] | None:
    """Return stored visible column names, or None if not set."""
    result: list[str] | None = session.get(_session_key(table_name))
    return result


def set_column_preference(session: Any, table_name: str, columns: list[str]) -> None:
    """Store visible column names in session."""
    session[_session_key(table_name)] = columns


class RequestConfig:
    """
    A configurator that uses request data to setup a table.

    A single RequestConfig can be used for multiple tables in one view.

    Arguments:
        paginate (dict or bool): Indicates whether to paginate, and if so, what
            default values to use. If the value evaluates to `False`, pagination
            will be disabled. A `dict` can be used to specify default values for
            the call to `~.tables.Table.paginate` (e.g. to define a default
            `per_page` value).

            A special *silent* item can be used to enable automatic handling of
            pagination exceptions using the following logic:

             - If `~django.core.paginator.PageNotAnInteger` is raised, show the first page.
             - If `~django.core.paginator.EmptyPage` is raised, show the last page.

            For example, to use `~.LazyPaginator`::

                RequestConfig(paginate={"paginator_class": LazyPaginator}).configure(table)

    """

    def __init__(self, request: HttpRequest, paginate: dict[str, Any] | bool = True) -> None:
        self.request = request
        self.paginate = paginate

    def configure(self, table: Any) -> Any:
        """
        Configure a table using information from the request.

        Arguments:
            table (`~.Table`): table to be configured
        """
        table.request = self.request

        # Column selection (before sorting/pagination so column count is settled)
        if getattr(table, "enable_column_selection", False) and table.table_name:
            self._configure_columns(table)

        order_by = self.request.GET.getlist(table.prefixed_order_by_field)
        if order_by:
            table.order_by = order_by
        if self.paginate:
            if isinstance(self.paginate, dict):
                kwargs: dict[str, Any] = dict(self.paginate)
            else:
                kwargs = {}
            # extract some options from the request
            for arg in ("page", "per_page"):
                name = getattr(table, f"prefixed_{arg}_field")
                try:
                    kwargs[arg] = int(self.request.GET[name])
                except (ValueError, KeyError):
                    pass

            silent = kwargs.pop("silent", True)
            if not silent:
                table.paginate(**kwargs)
            else:
                try:
                    table.paginate(**kwargs)
                except PageNotAnInteger:
                    table.page = table.paginator.page(1)
                except EmptyPage:
                    table.page = table.paginator.page(table.paginator.num_pages)

        return table

    def _configure_columns(self, table: Any) -> None:
        """Apply column visibility from request param or session."""
        session = self.request.session
        pinned: tuple[str, ...] = getattr(table, "pinned_columns", ())

        # All declared column names (preserving definition order, including hidden)
        all_column_names = [col.name for col in table.columns.iterall()]
        all_names_set = set(all_column_names)

        # Check for column selection form submission (sentinel hidden input)
        # Column form submits via POST (@post with contentType: 'form')
        post_data = self.request.POST
        is_column_submit = COLUMN_SELECTION_SUBMIT in post_data
        if is_column_submit:
            # Form sends multiple _columns values (one per checked checkbox)
            requested = [
                c.strip()
                for c in post_data.getlist(COLUMN_SELECTION_PARAM)
                if c.strip()
            ]
            valid = [name for name in requested if name in all_names_set]

            # Enforce pinned columns are always included
            for pin in pinned:
                if pin in all_names_set and pin not in valid:
                    valid.append(pin)

            # Enforce at least one column visible
            if not valid:
                valid = [all_column_names[0]]

            set_column_preference(session, table.table_name, valid)
            visible_names = valid
        else:
            # Read from session
            stored = get_column_preference(session, table.table_name)
            if stored is not None:
                # Filter out names that no longer exist in the table
                visible_names = [name for name in stored if name in all_names_set]
                # Enforce pinned
                for pin in pinned:
                    if pin in all_names_set and pin not in visible_names:
                        visible_names.append(pin)
                if not visible_names:
                    visible_names = [all_column_names[0]]
            else:
                # First visit: all default-visible columns
                visible_names = all_column_names

        # Apply visibility using django-tables2 show/hide API
        visible_set = set(visible_names)
        for name in all_column_names:
            if name in visible_set:
                table.columns.show(name)
            else:
                table.columns.hide(name)

        # Build all_columns_meta for template selector (all columns, not just visible)
        table.all_columns_meta = [
            {
                "name": col.name,
                "header": col.header,
                "visible": col.name in visible_set,
                "pinned": col.name in pinned,
            }
            for col in table.columns.iterall()
        ]
