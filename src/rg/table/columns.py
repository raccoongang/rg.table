"""Dynamic column support."""

from collections.abc import Callable
from typing import Any

import django_tables2 as tables


class DynamicColumn(tables.Column):
    """
    A column that can be dynamically configured at runtime.

    Example:
        table = MyTable(data, extra_columns=[
            DynamicColumn(name="custom", accessor="get_custom_value"),
        ])
    """

    def __init__(
        self,
        name: str | None = None,
        accessor: str | Callable[..., Any] | None = None,
        **kwargs: Any,
    ) -> None:
        self.dynamic_name = name
        super().__init__(accessor=accessor, **kwargs)
