"""rg.table4 - Django table rendering helper."""

__version__ = "0.1.0"

from .columns import DynamicColumn
from .tables import Table4, Table4Meta
from .views import table_render
from .config import RequestConfig

__all__ = [
    "Table4",
    "Table4Meta",
    "Table4Mixin",
    "Table4ListView",
    "DynamicColumn",
    "RequestConfig",
    "table_render",
    "__version__",
]
