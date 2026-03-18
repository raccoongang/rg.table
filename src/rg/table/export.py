"""Row actions, export helpers, and ExportMixin for rg.table."""

from __future__ import annotations

import csv
import io
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from django.http import HttpResponse
from django.utils.translation import gettext as _

if TYPE_CHECKING:
    from django.http import HttpRequest


@dataclass(frozen=True)
class TableAction:
    """A bulk action that can be applied to selected table rows.

    Attributes:
        name: Unique identifier (e.g. "delete", "export_csv").
        label: Display text shown in the action dropdown.
        handler: Callable with signature
            ``(request, table, selected_pks: list[str]) -> HttpResponse | None``.
            Return ``HttpResponse`` for downloads, ``None`` to redirect back (PRG).
        requires_selection: If True, the handler is skipped when nothing is selected.
        confirm: Optional browser ``confirm()`` message shown before executing.
    """

    name: str
    label: str
    handler: Callable[..., HttpResponse | None]
    requires_selection: bool = True
    confirm: str | None = None


def _get_row_id(table: Any, row: Any) -> Any:
    """Extract row ID using ``table.row_id_field``."""
    field: str = getattr(table, "row_id_field", "pk")
    record = row.record
    if hasattr(record, field):
        return getattr(record, field)
    return record[field]


def _export_columns(table: Any) -> list[Any]:
    """Return visible columns that are not marked ``exclude_from_export``."""
    return [
        col
        for col in table.columns
        if not getattr(col.column, "exclude_from_export", False)
    ]


def _record_attr(record: Any, attr: str, default: Any = "") -> Any:
    """Read *attr* from a record (model instance or dict)."""
    if hasattr(record, attr):
        return getattr(record, attr)
    try:
        return record[attr]
    except (KeyError, TypeError):
        return default


def make_csv_export(
    filename: str = "export.csv",
    extra_fields: list[tuple[str, str]] | None = None,
) -> Callable[..., HttpResponse]:
    """Create a CSV export action handler using visible table columns.

    If *selected_pks* is empty the handler exports **all** rows.

    *extra_fields* is an optional list of ``(header, attr_name)`` tuples.
    For each row the value is read via ``getattr(row.record, attr_name, "")``.
    Extra fields are appended after the regular table columns.
    """

    def handler(
        request: HttpRequest, table: Any, selected_pks: list[str]
    ) -> HttpResponse:
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)
        columns = _export_columns(table)
        headers = [col.header for col in columns]
        extras = extra_fields or []
        headers.extend(str(hdr) for hdr, _attr in extras)
        writer.writerow(headers)
        selected_set = set(selected_pks)
        for row in table.rows:
            rid = str(_get_row_id(table, row))
            if not selected_set or rid in selected_set:
                values = [row.get_cell_value(col.name) for col in columns]
                for _, attr in extras:
                    values.append(_record_attr(row.record, attr))
                writer.writerow(values)
        return response

    return handler


def make_xlsx_export(
    filename: str = "export.xlsx",
    extra_fields: list[tuple[str, str]] | None = None,
) -> Callable[..., HttpResponse]:
    """Create an XLSX export action handler using visible table columns.

    Requires the ``xlsxwriter`` package.  If *selected_pks* is empty the
    handler exports **all** rows.

    *extra_fields* is an optional list of ``(header, attr_name)`` tuples.
    For each row the value is read via ``getattr(row.record, attr_name, "")``.
    Extra fields are appended after the regular table columns.
    """

    def handler(
        request: HttpRequest, table: Any, selected_pks: list[str]
    ) -> HttpResponse:
        import xlsxwriter

        buf = io.BytesIO()
        wb = xlsxwriter.Workbook(buf, {"in_memory": True})
        ws = wb.add_worksheet("Export")
        bold = wb.add_format({"bold": True})

        columns = _export_columns(table)
        headers = [str(col.header) for col in columns]
        extras = extra_fields or []
        headers.extend(str(hdr) for hdr, _attr in extras)
        for col_idx, header in enumerate(headers):
            ws.write(0, col_idx, header, bold)

        selected_set = set(selected_pks)
        row_idx = 1
        for row in table.rows:
            rid = str(_get_row_id(table, row))
            if not selected_set or rid in selected_set:
                for col_idx, col in enumerate(columns):
                    value = row.get_cell_value(col.name)
                    if not isinstance(value, (str, int, float, bool, type(None))):
                        value = str(value)
                    ws.write(row_idx, col_idx, value)
                col_offset = len(columns)
                for extra_idx, (_, attr) in enumerate(extras):
                    value = _record_attr(row.record, attr)
                    if not isinstance(value, (str, int, float, bool, type(None))):
                        value = str(value)
                    ws.write(row_idx, col_offset + extra_idx, value)
                row_idx += 1

        for col_idx, header in enumerate(headers):
            ws.set_column(col_idx, col_idx, max(len(str(header)) + 2, 12))

        wb.close()
        response = HttpResponse(
            buf.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    return handler


class ExportMixin:
    """Mixin that adds CSV and XLSX export actions to any table.

    Appends export actions *after* any actions defined in Meta / constructor.
    XLSX is only added if ``xlsxwriter`` is installed.

    Example::

        class MyTable(ExportMixin, Table):
            class Meta(TableMeta):
                actions = (
                    TableAction("delete", "Delete selected", delete_handler),
                )
            # Result: actions = (delete, export_csv, export_xlsx)
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        existing: tuple[Any, ...] = getattr(self, "actions", ())
        export_actions: list[TableAction] = [
            TableAction(
                "export_csv",
                _("Export CSV"),
                make_csv_export(),
                requires_selection=False,
            ),
        ]
        try:
            import xlsxwriter  # noqa: F401

            export_actions.append(
                TableAction(
                    "export_xlsx",
                    _("Export XLSX"),
                    make_xlsx_export(),
                    requires_selection=False,
                ),
            )
        except ImportError:
            pass
        self.actions = tuple(existing) + tuple(export_actions)
