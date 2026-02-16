from typing import Any

from django.core.paginator import EmptyPage, PageNotAnInteger
from django.http import HttpRequest

COLUMN_SELECTION_PARAM = "_columns"
COLUMN_SELECTION_SUBMIT = "_columns_submit"
SESSION_KEY_PREFIX = "rg_table:columns"
PER_PAGE_SESSION_KEY_PREFIX = "rg_table:per_page"
SORT_SESSION_KEY_PREFIX = "rg_table:sort"
ACTIVE_PROFILE_KEY_PREFIX = "rg_table:active_profile"
PROFILE_ACTION_PARAM = "_profile_action"
PROFILE_ID_PARAM = "_profile_id"
PROFILE_NAME_PARAM = "_profile_name"
PER_PAGE_SUBMIT_PARAM = "_per_page_submit"
PER_PAGE_VALUE_PARAM = "_per_page"


def _session_key(table_name: str) -> str:
    return f"{SESSION_KEY_PREFIX}:{table_name}"


def get_column_preference(session: Any, table_name: str) -> list[str] | None:
    """Return stored visible column names, or None if not set."""
    result: list[str] | None = session.get(_session_key(table_name))
    return result


def set_column_preference(session: Any, table_name: str, columns: list[str]) -> None:
    """Store visible column names in session."""
    session[_session_key(table_name)] = columns


def get_per_page_preference(session: Any, table_name: str) -> int | None:
    """Return stored per_page preference, or None if not set."""
    result: int | None = session.get(f"{PER_PAGE_SESSION_KEY_PREFIX}:{table_name}")
    return result


def set_per_page_preference(session: Any, table_name: str, per_page: int) -> None:
    """Store per_page preference in session."""
    session[f"{PER_PAGE_SESSION_KEY_PREFIX}:{table_name}"] = per_page


def get_sort_preference(session: Any, table_name: str) -> list[str] | None:
    """Return stored sort order preference, or None if not set."""
    result: list[str] | None = session.get(f"{SORT_SESSION_KEY_PREFIX}:{table_name}")
    return result


def set_sort_preference(session: Any, table_name: str, sort_order: list[str]) -> None:
    """Store sort order preference in session."""
    session[f"{SORT_SESSION_KEY_PREFIX}:{table_name}"] = sort_order


def get_active_profile_info(session: Any, table_name: str) -> dict[str, Any] | None:
    """Return active profile metadata from session, or None."""
    result: dict[str, Any] | None = session.get(
        f"{ACTIVE_PROFILE_KEY_PREFIX}:{table_name}"
    )
    return result


def set_active_profile_info(
    session: Any, table_name: str, profile_id: int, name: str
) -> None:
    """Store active profile metadata in session."""
    session[f"{ACTIVE_PROFILE_KEY_PREFIX}:{table_name}"] = {
        "id": profile_id,
        "name": name,
    }


def clear_active_profile_info(session: Any, table_name: str) -> None:
    """Remove active profile metadata from session."""
    session.pop(f"{ACTIVE_PROFILE_KEY_PREFIX}:{table_name}", None)


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

        # 1. Profile actions (save/load/delete) - before everything else
        if getattr(table, "enable_profiles", False) and table.table_name:
            self._handle_profile_action(table)

        # 2. Auto-load default profile on first visit (authenticated user)
        if getattr(table, "enable_profiles", False) and table.table_name:
            self._maybe_load_default_profile(table)

        # 3. Column selection (before sorting/pagination so column count is settled)
        if getattr(table, "enable_column_selection", False) and table.table_name:
            self._configure_columns(table)

        # 4. Per-page selection from POST
        if getattr(table, "enable_per_page_selection", False) and table.table_name:
            self._configure_per_page(table)

        # 5. Order by
        order_by = self.request.GET.getlist(table.prefixed_order_by_field)
        if order_by:
            table.order_by = order_by

        # 6. Paginate
        if self.paginate:
            if isinstance(self.paginate, dict):
                kwargs: dict[str, Any] = dict(self.paginate)
            else:
                kwargs = {}

            # Apply per_page from session if available
            if getattr(table, "enable_per_page_selection", False) and table.table_name:
                session_per_page = get_per_page_preference(
                    self.request.session, table.table_name
                )
                if session_per_page is not None:
                    kwargs["per_page"] = session_per_page

            # extract some options from the request (URL params override session)
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

            # Track current per_page for template highlight
            if getattr(table, "enable_per_page_selection", False):
                table.current_per_page = table.paginator.per_page

        # 7. Build profile metadata for templates
        if getattr(table, "enable_profiles", False) and table.table_name:
            self._build_profile_meta(table)

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

    def _handle_profile_action(self, table: Any) -> None:
        """Check POST for _profile_action and dispatch to profile helpers."""
        from .profiles import (
            delete_profile,
            load_profile,
            save_as_profile,
            save_profile,
            set_default_profile,
        )

        post_data = self.request.POST
        action = post_data.get(PROFILE_ACTION_PARAM)
        if not action:
            return

        user = self.request.user
        if not user or not getattr(user, "is_authenticated", False):
            return

        session = self.request.session
        table_name = table.table_name

        if action == "save":
            active = get_active_profile_info(session, table_name)
            if active:
                save_profile(session, user, table_name, active["id"])

        elif action == "save_as":
            name = post_data.get(PROFILE_NAME_PARAM, "").strip()
            if name:
                save_as_profile(session, user, table_name, name)

        elif action == "load":
            profile_id = post_data.get(PROFILE_ID_PARAM)
            if profile_id:
                from .models import TableProfile

                try:
                    profile = TableProfile.objects.get(
                        id=int(profile_id), user=user
                    )
                    load_profile(session, profile)
                except (TableProfile.DoesNotExist, ValueError):
                    pass

        elif action == "delete":
            profile_id = post_data.get(PROFILE_ID_PARAM)
            if profile_id:
                try:
                    delete_profile(int(profile_id), user)
                    # Clear active profile if deleted profile was active
                    active = get_active_profile_info(session, table_name)
                    if active and active["id"] == int(profile_id):
                        clear_active_profile_info(session, table_name)
                except (ValueError, TypeError):
                    pass

        elif action == "set_default":
            profile_id = post_data.get(PROFILE_ID_PARAM)
            if profile_id:
                try:
                    set_default_profile(int(profile_id), user, table_name)
                except (ValueError, TypeError):
                    pass

    def _maybe_load_default_profile(self, table: Any) -> None:
        """On first visit (no active profile in session), load default profile."""
        user = self.request.user
        if not user or not getattr(user, "is_authenticated", False):
            return

        session = self.request.session
        table_name = table.table_name

        # Only auto-load if no active profile is set yet
        if get_active_profile_info(session, table_name) is not None:
            return

        from .profiles import get_default_profile, load_profile

        default = get_default_profile(user, table_name)
        if default:
            load_profile(session, default)

    def _configure_per_page(self, table: Any) -> None:
        """Handle per_page selection from POST and store in session."""
        post_data = self.request.POST
        if PER_PAGE_SUBMIT_PARAM not in post_data:
            return

        session = self.request.session
        try:
            per_page = int(post_data.get(PER_PAGE_VALUE_PARAM, ""))
        except (ValueError, TypeError):
            return

        allowed = getattr(table, "per_page_choices", ())
        if allowed and per_page not in allowed:
            return

        set_per_page_preference(session, table.table_name, per_page)

    def _build_profile_meta(self, table: Any) -> None:
        """Set table.profiles_list and table.active_profile for template use."""
        user = self.request.user
        if not user or not getattr(user, "is_authenticated", False):
            table.profiles_list = []
            table.active_profile = None
            return

        from .profiles import list_profiles

        profiles = list_profiles(user, table.table_name)
        table.profiles_list = [
            {"id": p.pk, "name": p.name, "is_default": p.is_default}
            for p in profiles
        ]
        table.active_profile = get_active_profile_info(
            self.request.session, table.table_name
        )
