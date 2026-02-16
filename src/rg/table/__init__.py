"""rg.table - Django table rendering helper."""

from __future__ import annotations

from typing import TYPE_CHECKING

__version__ = "0.1.0"

from .columns import DynamicColumn
from .config import RequestConfig
from .tables import Table, TableMeta
from .views import table_render

if TYPE_CHECKING:
    from .models import TableProfile

__all__ = [
    "Table",
    "TableMeta",
    "TableProfile",
    "TableMixin",
    "TableListView",
    "DynamicColumn",
    "RequestConfig",
    "table_render",
    "__version__",
]


def __getattr__(name: str) -> type:
    if name == "TableProfile":
        from .models import TableProfile

        return TableProfile
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
