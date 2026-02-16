"""Profile CRUD helpers for rg.table."""

from __future__ import annotations

from typing import Any

from django.db.models import QuerySet

from .config import (
    get_column_preference,
    get_per_page_preference,
    get_sort_preference,
    set_active_profile_info,
    set_column_preference,
    set_per_page_preference,
    set_sort_preference,
)
from .models import TableProfile


def list_profiles(user: Any, table_name: str) -> QuerySet[TableProfile]:
    """Return all profiles for a user/table combination."""
    return TableProfile.objects.filter(user=user, table_name=table_name)


def save_profile(
    session: Any, user: Any, table_name: str, profile_id: int
) -> TableProfile | None:
    """Update an existing profile from current session state.

    Returns the updated profile, or None if not found / not owned by user.
    """
    try:
        profile = TableProfile.objects.get(id=profile_id, user=user)
    except TableProfile.DoesNotExist:
        return None

    columns = get_column_preference(session, table_name)
    if columns is not None:
        profile.columns = columns
    profile.per_page = get_per_page_preference(session, table_name)
    profile.sort_order = get_sort_preference(session, table_name) or []
    profile.save()

    set_active_profile_info(session, table_name, profile.pk, profile.name)
    return profile


def save_as_profile(
    session: Any, user: Any, table_name: str, name: str
) -> TableProfile:
    """Create a new profile from current session state."""
    columns = get_column_preference(session, table_name) or []
    per_page = get_per_page_preference(session, table_name)
    sort_order = get_sort_preference(session, table_name) or []

    profile = TableProfile.objects.create(
        user=user,
        table_name=table_name,
        name=name,
        columns=columns,
        per_page=per_page,
        sort_order=sort_order,
    )
    set_active_profile_info(session, table_name, profile.pk, profile.name)
    return profile


def load_profile(session: Any, profile: TableProfile) -> None:
    """Write profile data into session keys."""
    table_name = profile.table_name

    if profile.columns:
        set_column_preference(session, table_name, profile.columns)
    if profile.per_page is not None:
        set_per_page_preference(session, table_name, profile.per_page)
    if profile.sort_order:
        set_sort_preference(session, table_name, profile.sort_order)

    set_active_profile_info(session, table_name, profile.pk, profile.name)


def delete_profile(profile_id: int, user: Any) -> bool:
    """Delete a profile. Returns True if deleted, False if not found."""
    deleted, _ = TableProfile.objects.filter(id=profile_id, user=user).delete()
    return deleted > 0


def set_default_profile(profile_id: int, user: Any, table_name: str) -> None:
    """Set one profile as default, unset others for the same user/table."""
    TableProfile.objects.filter(user=user, table_name=table_name).update(
        is_default=False
    )
    TableProfile.objects.filter(id=profile_id, user=user).update(is_default=True)


def get_default_profile(user: Any, table_name: str) -> TableProfile | None:
    """Return the user's default profile for a table, or None."""
    return (
        TableProfile.objects.filter(
            user=user, table_name=table_name, is_default=True
        ).first()
    )
