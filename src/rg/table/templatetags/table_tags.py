"""Template tags for rg.table."""

from typing import Any

from django import template

register = template.Library()


@register.simple_tag
def row_id(table: Any, row: Any) -> Any:
    """Return the row ID value for a selection checkbox.

    Uses ``table.row_id_field`` (default ``"pk"``) to extract the identifier
    from the row's underlying record.

    Usage::

        {% load table_tags %}
        {% row_id table row as rid %}
        <input type="checkbox" value="{{ rid }}">
    """
    field: str = getattr(table, "row_id_field", "pk")
    record = row.record
    if hasattr(record, field):
        return getattr(record, field)
    return record[field]
