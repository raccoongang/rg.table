"""Tests for row selection & actions (TableAction, export, templates, views)."""

from __future__ import annotations

import csv
import io
import json
from unittest.mock import MagicMock

import django_tables2 as tables
import pytest
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.test import RequestFactory

from rg.table import RequestConfig, Table, TableAction, TableMeta
from rg.table.config import (
    ACTION_PARAM,
    ACTION_SUBMIT_PARAM,
    SELECTION_PARAM,
)
from rg.table.export import ExportMixin, _get_row_id, make_csv_export, make_xlsx_export
from rg.table.views import table_render

# --- Test table classes ---


def _noop_handler(request, table, selected_pks):
    return None


DELETE_ACTION = TableAction("delete", "Delete selected", _noop_handler)
EXPORT_ACTION = TableAction(
    "export", "Export", _noop_handler, requires_selection=False
)


class ActionTable(Table):
    id = tables.Column()
    name = tables.Column()
    country = tables.Column()

    class Meta(TableMeta):
        template_kit = "bootstrap"
        actions = (DELETE_ACTION,)
        row_id_field = "id"


class NoActionTable(Table):
    id = tables.Column()
    name = tables.Column()

    class Meta(TableMeta):
        template_kit = "bootstrap"


class CustomIdTable(Table):
    code = tables.Column()
    name = tables.Column()

    class Meta(TableMeta):
        template_kit = "bootstrap"
        actions = (DELETE_ACTION,)
        row_id_field = "code"


class BulmaActionTable(Table):
    id = tables.Column()
    name = tables.Column()

    class Meta(TableMeta):
        template_kit = "bulma"
        actions = (DELETE_ACTION,)
        row_id_field = "id"


class ExportTable(ExportMixin, Table):
    id = tables.Column()
    name = tables.Column()
    country = tables.Column()

    class Meta(TableMeta):
        template_kit = "bootstrap"
        actions = (DELETE_ACTION,)
        row_id_field = "id"


class InfiniteActionTable(Table):
    id = tables.Column()
    name = tables.Column()

    class Meta(TableMeta):
        template_kit = "bootstrap"
        infinite_scroll = True
        actions = (DELETE_ACTION,)
        row_id_field = "id"


# --- Fixtures ---

SAMPLE_DATA = [
    {"id": 1, "name": "Alice", "country": "USA"},
    {"id": 2, "name": "Bob", "country": "UK"},
    {"id": 3, "name": "Charlie", "country": "Canada"},
    {"id": 4, "name": "Diana", "country": "Australia"},
    {"id": 5, "name": "Eve", "country": "Germany"},
]


@pytest.fixture
def rf():
    return RequestFactory()


def _make_request(rf, get_params=None, post_params=None, datastar=False):
    """Create a request with session dict."""
    if post_params is not None:
        request = rf.post("/test/", data=post_params)
        if datastar:
            request.META["HTTP_DATASTAR_REQUEST"] = "true"
    else:
        request = rf.get("/test/", data=get_params or {})
        if datastar:
            request.META["HTTP_DATASTAR_REQUEST"] = "true"
    request.session = {}
    request.user = MagicMock(is_authenticated=False)
    return request


# --- TableAction tests ---


class TestTableAction:
    def test_creation(self):
        action = TableAction("test", "Test Action", _noop_handler)
        assert action.name == "test"
        assert action.label == "Test Action"
        assert action.handler is _noop_handler
        assert action.requires_selection is True

    def test_requires_selection_false(self):
        action = TableAction("test", "Test", _noop_handler, requires_selection=False)
        assert action.requires_selection is False

    def test_frozen(self):
        action = TableAction("test", "Test", _noop_handler)
        with pytest.raises(AttributeError):
            action.name = "other"  # type: ignore[misc]


# --- Table Meta & constructor tests ---


class TestTableMetaOptions:
    def test_actions_from_meta(self):
        table = ActionTable(SAMPLE_DATA, name="test")
        assert len(table.actions) == 1
        assert table.actions[0].name == "delete"

    def test_actions_from_kwarg(self):
        table = NoActionTable(SAMPLE_DATA, name="test", actions=(EXPORT_ACTION,))
        assert len(table.actions) == 1
        assert table.actions[0].name == "export"

    def test_no_actions_default(self):
        table = NoActionTable(SAMPLE_DATA, name="test")
        assert table.actions == ()

    def test_row_id_field_from_meta(self):
        table = ActionTable(SAMPLE_DATA, name="test")
        assert table.row_id_field == "id"

    def test_row_id_field_from_kwarg(self):
        table = NoActionTable(SAMPLE_DATA, name="test", row_id_field="name")
        assert table.row_id_field == "name"

    def test_row_id_field_default(self):
        table = NoActionTable(SAMPLE_DATA, name="test")
        assert table.row_id_field == "pk"

    def test_visible_ids_json_default(self):
        table = ActionTable(SAMPLE_DATA, name="test")
        assert table.visible_ids_json == "[]"


# --- Row ID extraction ---


class TestRowId:
    def test_get_row_id_dict(self):
        table = ActionTable(SAMPLE_DATA, name="test")
        RequestConfig(
            _make_request(RequestFactory()), paginate={"per_page": 25}
        ).configure(table)
        row = list(table.rows)[0]
        assert str(_get_row_id(table, row)) == "1"

    def test_get_row_id_custom_field(self):
        data = [{"code": "A1", "name": "Test"}]
        table = CustomIdTable(data, name="test")
        RequestConfig(
            _make_request(RequestFactory()), paginate={"per_page": 25}
        ).configure(table)
        row = list(table.rows)[0]
        assert _get_row_id(table, row) == "A1"


# --- RequestConfig: _build_visible_ids ---


class TestBuildVisibleIds:
    def test_visible_ids_populated(self, rf):
        request = _make_request(rf)
        table = ActionTable(SAMPLE_DATA, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)
        ids = json.loads(table.visible_ids_json)
        assert ids == ["1", "2", "3", "4", "5"]

    def test_visible_ids_paginated(self, rf):
        request = _make_request(rf)
        table = ActionTable(SAMPLE_DATA, name="test")
        RequestConfig(request, paginate={"per_page": 2}).configure(table)
        ids = json.loads(table.visible_ids_json)
        assert ids == ["1", "2"]

    def test_no_visible_ids_without_actions(self, rf):
        request = _make_request(rf)
        table = NoActionTable(SAMPLE_DATA, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)
        assert table.visible_ids_json == "[]"

    def test_custom_row_id_field(self, rf):
        data = [{"code": "X1", "name": "Test1"}, {"code": "X2", "name": "Test2"}]
        request = _make_request(rf)
        table = CustomIdTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)
        ids = json.loads(table.visible_ids_json)
        assert ids == ["X1", "X2"]


# --- Template rendering ---


class TestActionBarTemplate:
    def _render(self, table, rf, kit="bootstrap"):
        request = _make_request(rf)
        RequestConfig(request, paginate={"per_page": 25}).configure(table)
        html = render_to_string(
            f"rg_table/{kit}/table.html", {"table": table, "request": request}, request
        )
        return html

    def test_action_bar_rendered(self, rf):
        table = ActionTable(SAMPLE_DATA, name="test")
        html = self._render(table, rf)
        assert "Select all" in html
        assert "_action" in html
        assert "Delete selected" in html
        assert 'name="_action_submit"' in html

    def test_no_action_bar_without_actions(self, rf):
        table = NoActionTable(SAMPLE_DATA, name="test")
        html = self._render(table, rf)
        assert "Select all" not in html
        assert "_action_submit" not in html

    def test_wrapping_form_present(self, rf):
        table = ActionTable(SAMPLE_DATA, name="test")
        html = self._render(table, rf)
        assert '<form method="post"' in html

    def test_no_wrapping_form_without_actions(self, rf):
        table = NoActionTable(SAMPLE_DATA, name="test")
        html = self._render(table, rf)
        assert '<form method="post"' not in html

    def test_selection_signal_declared(self, rf):
        table = ActionTable(SAMPLE_DATA, name="test")
        html = self._render(table, rf)
        assert "tabletestSelectAll: false" in html

    def test_no_signal_without_actions(self, rf):
        table = NoActionTable(SAMPLE_DATA, name="test")
        html = self._render(table, rf)
        assert "tabletestSelectAll" not in html

    def test_bulma_action_bar(self, rf):
        table = BulmaActionTable(SAMPLE_DATA, name="test")
        html = self._render(table, rf, kit="bulma")
        assert "Select all" in html
        assert "Delete selected" in html


class TestCheckboxColumn:
    def _render(self, table, rf, kit="bootstrap"):
        request = _make_request(rf)
        RequestConfig(request, paginate={"per_page": 25}).configure(table)
        html = render_to_string(
            f"rg_table/{kit}/table_body.html",
            {"table": table, "request": request},
            request,
        )
        return html

    def test_checkboxes_rendered(self, rf):
        table = ActionTable(SAMPLE_DATA, name="test")
        html = self._render(table, rf)
        assert 'name="_selected"' in html
        assert 'value="1"' in html
        assert 'value="5"' in html
        assert "$tabletestSelectAll" in html

    def test_no_checkboxes_without_actions(self, rf):
        table = NoActionTable(SAMPLE_DATA, name="test")
        html = self._render(table, rf)
        assert 'name="_selected"' not in html

    def test_empty_header_th(self, rf):
        table = ActionTable(SAMPLE_DATA, name="test")
        html = self._render(table, rf)
        # Check for the empty th (width: 1%)
        assert 'style="width: 1%;"' in html

    def test_bulma_checkboxes(self, rf):
        table = BulmaActionTable(SAMPLE_DATA, name="test")
        html = self._render(table, rf, kit="bulma")
        assert 'name="_selected"' in html


# --- Action dispatch in table_render ---


class TestActionDispatch:
    def test_action_handler_called(self, rf):
        handler = MagicMock(return_value=None)
        action = TableAction("test", "Test", handler)
        table = ActionTable(SAMPLE_DATA, name="test", actions=(action,))
        request = _make_request(
            rf,
            post_params={
                ACTION_SUBMIT_PARAM: "1",
                ACTION_PARAM: "test",
                SELECTION_PARAM: ["1", "3"],
            },
        )
        RequestConfig(request, paginate={"per_page": 25}).configure(table)
        response = table_render(request, "test.html", {"table": table})
        handler.assert_called_once_with(request, table, ["1", "3"])
        assert response.status_code == 302  # redirect

    def test_download_action_returns_response(self, rf):
        csv_response = HttpResponse("data", content_type="text/csv")

        def download_handler(request, table, selected_pks):
            return csv_response

        action = TableAction("dl", "Download", download_handler)
        table = ActionTable(SAMPLE_DATA, name="test", actions=(action,))
        request = _make_request(
            rf,
            post_params={
                ACTION_SUBMIT_PARAM: "1",
                ACTION_PARAM: "dl",
                SELECTION_PARAM: ["1"],
            },
        )
        RequestConfig(request, paginate={"per_page": 25}).configure(table)
        response = table_render(request, "test.html", {"table": table})
        assert response is csv_response

    def test_requires_selection_skips_empty(self, rf):
        handler = MagicMock(return_value=None)
        action = TableAction("test", "Test", handler, requires_selection=True)
        table = ActionTable(SAMPLE_DATA, name="test", actions=(action,))
        request = _make_request(
            rf,
            post_params={ACTION_SUBMIT_PARAM: "1", ACTION_PARAM: "test"},
        )
        RequestConfig(request, paginate={"per_page": 25}).configure(table)
        response = table_render(
            request,
            "rg_table/bootstrap/table.html",
            {"table": table, "request": request},
        )
        handler.assert_not_called()
        # Renders page with empty selection message instead of redirecting
        assert response.status_code == 200
        assert table.empty_selection_message is not None

    def test_requires_selection_false_runs_empty(self, rf):
        handler = MagicMock(return_value=None)
        action = TableAction("test", "Test", handler, requires_selection=False)
        table = ActionTable(SAMPLE_DATA, name="test", actions=(action,))
        request = _make_request(
            rf,
            post_params={ACTION_SUBMIT_PARAM: "1", ACTION_PARAM: "test"},
        )
        RequestConfig(request, paginate={"per_page": 25}).configure(table)
        table_render(request, "test.html", {"table": table})
        handler.assert_called_once_with(request, table, [])

    def test_unknown_action_redirects(self, rf):
        table = ActionTable(SAMPLE_DATA, name="test")
        request = _make_request(
            rf,
            post_params={ACTION_SUBMIT_PARAM: "1", ACTION_PARAM: "nonexistent"},
        )
        RequestConfig(request, paginate={"per_page": 25}).configure(table)
        response = table_render(request, "test.html", {"table": table})
        assert response.status_code == 302



# --- Selection signal clearing on page change ---


class TestSelectionClearing:
    def test_signal_cleared_on_paginated_get(self, rf):
        table = ActionTable(SAMPLE_DATA, name="test")
        request = _make_request(rf, get_params={"page": "1"}, datastar=True)
        RequestConfig(request, paginate={"per_page": 25}).configure(table)
        response = table_render(
            request,
            "test.html",
            {"table": table, "request": request},
        )
        content = b"".join(response.streaming_content).decode()
        # Should have patch_signals clearing select-all
        assert "tabletestSelectAll" in content

    def test_signal_not_cleared_on_infinite_scroll(self, rf):
        table = InfiniteActionTable(SAMPLE_DATA, name="test")
        request = _make_request(rf, get_params={"page": "1"}, datastar=True)
        RequestConfig(request, paginate={"per_page": 25}).configure(table)
        response = table_render(
            request,
            "test.html",
            {"table": table, "request": request},
        )
        content = b"".join(response.streaming_content).decode()
        # Should NOT have patch-signals clearing selection for infinite scroll
        # (the signal name will appear in template HTML via data-model, but
        #  there should be no datastar-patch-signals event clearing it)
        assert "datastar-patch-signals" not in content


# --- CSV export ---


class TestMakeCsvExport:
    def test_csv_export_all_rows(self, rf):
        handler = make_csv_export("test.csv")
        request = _make_request(rf)
        table = ActionTable(SAMPLE_DATA, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)
        response = handler(request, table, [])
        assert response["Content-Type"] == "text/csv"
        assert 'filename="test.csv"' in response["Content-Disposition"]
        content = response.content.decode()
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        assert rows[0] == ["Id", "Name", "Country"]  # headers (django-tables2 title case)
        assert len(rows) == 6  # header + 5 data rows

    def test_csv_export_selected_only(self, rf):
        handler = make_csv_export()
        request = _make_request(rf)
        table = ActionTable(SAMPLE_DATA, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)
        response = handler(request, table, ["1", "3"])
        content = response.content.decode()
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        assert len(rows) == 3  # header + 2 selected


# --- XLSX export ---


class TestMakeXlsxExport:
    def test_xlsx_export(self, rf):
        pytest.importorskip("xlsxwriter")
        handler = make_xlsx_export("test.xlsx")
        request = _make_request(rf)
        table = ActionTable(SAMPLE_DATA, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)
        response = handler(request, table, [])
        assert (
            response["Content-Type"]
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        assert 'filename="test.xlsx"' in response["Content-Disposition"]
        assert len(response.content) > 0

    def test_xlsx_export_selected(self, rf):
        pytest.importorskip("xlsxwriter")
        handler = make_xlsx_export()
        request = _make_request(rf)
        table = ActionTable(SAMPLE_DATA, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)
        response = handler(request, table, ["2"])
        assert len(response.content) > 0


# --- ExportMixin ---


class TestExportMixin:
    def test_mixin_appends_csv(self):
        table = ExportTable(SAMPLE_DATA, name="test")
        action_names = [a.name for a in table.actions]
        assert "delete" in action_names
        assert "export_csv" in action_names

    def test_mixin_csv_requires_selection_false(self):
        table = ExportTable(SAMPLE_DATA, name="test")
        csv_action = next(a for a in table.actions if a.name == "export_csv")
        assert csv_action.requires_selection is False

    def test_mixin_xlsx_if_xlsxwriter_installed(self):
        xlsxwriter = pytest.importorskip("xlsxwriter")  # noqa: F841
        table = ExportTable(SAMPLE_DATA, name="test")
        action_names = [a.name for a in table.actions]
        assert "export_xlsx" in action_names

    def test_mixin_preserves_meta_actions(self):
        table = ExportTable(SAMPLE_DATA, name="test")
        assert table.actions[0].name == "delete"  # from Meta
        # export actions come after


# --- Template tag: row_id ---


# --- Confirm field ---


class TestConfirmField:
    def test_confirm_default_none(self):
        action = TableAction("test", "Test", _noop_handler)
        assert action.confirm is None

    def test_confirm_set(self):
        action = TableAction("test", "Test", _noop_handler, confirm="Sure?")
        assert action.confirm == "Sure?"

    def test_action_confirms_json_populated(self, rf):
        confirm_action = TableAction(
            "del", "Delete", _noop_handler, confirm="Are you sure?"
        )
        no_confirm = TableAction(
            "exp", "Export", _noop_handler, requires_selection=False
        )
        table = ActionTable(
            SAMPLE_DATA, name="test", actions=(confirm_action, no_confirm)
        )
        request = _make_request(rf)
        RequestConfig(request, paginate={"per_page": 25}).configure(table)
        confirms = json.loads(table.action_confirms_json)
        assert confirms == {"del": "Are you sure?"}

    def test_action_confirms_json_empty(self, rf):
        table = ActionTable(SAMPLE_DATA, name="test")
        request = _make_request(rf)
        RequestConfig(request, paginate={"per_page": 25}).configure(table)
        confirms = json.loads(table.action_confirms_json)
        assert confirms == {}

    def test_no_action_confirms_without_actions(self, rf):
        table = NoActionTable(SAMPLE_DATA, name="test")
        request = _make_request(rf)
        RequestConfig(request, paginate={"per_page": 25}).configure(table)
        assert table.action_confirms_json == "{}"


# --- Empty selection guard ---


class TestEmptySelectionGuard:
    def test_empty_selection_renders_message(self, rf):
        handler = MagicMock(return_value=None)
        action = TableAction("del", "Delete", handler, requires_selection=True)
        table = ActionTable(SAMPLE_DATA, name="test", actions=(action,))
        request = _make_request(
            rf,
            post_params={ACTION_SUBMIT_PARAM: "1", ACTION_PARAM: "del"},
        )
        RequestConfig(request, paginate={"per_page": 25}).configure(table)
        response = table_render(
            request,
            "rg_table/bootstrap/table.html",
            {"table": table, "request": request},
        )
        handler.assert_not_called()
        assert response.status_code == 200
        assert table.empty_selection_message is not None

    def test_no_message_when_selection_present(self, rf):
        handler = MagicMock(return_value=None)
        action = TableAction("del", "Delete", handler, requires_selection=True)
        table = ActionTable(SAMPLE_DATA, name="test", actions=(action,))
        request = _make_request(
            rf,
            post_params={
                ACTION_SUBMIT_PARAM: "1",
                ACTION_PARAM: "del",
                SELECTION_PARAM: ["1"],
            },
        )
        RequestConfig(request, paginate={"per_page": 25}).configure(table)
        response = table_render(request, "test.html", {"table": table})
        handler.assert_called_once()
        assert response.status_code == 302
        assert table.empty_selection_message is None

    def test_no_message_for_requires_selection_false(self, rf):
        handler = MagicMock(return_value=None)
        action = TableAction("exp", "Export", handler, requires_selection=False)
        table = ActionTable(SAMPLE_DATA, name="test", actions=(action,))
        request = _make_request(
            rf,
            post_params={ACTION_SUBMIT_PARAM: "1", ACTION_PARAM: "exp"},
        )
        RequestConfig(request, paginate={"per_page": 25}).configure(table)
        table_render(request, "test.html", {"table": table})
        handler.assert_called_once()
        assert table.empty_selection_message is None

    def test_bulk_delete_guard_blocks_all_visible(self, rf):
        """Confirmed action on all visible rows is blocked."""
        handler = MagicMock(return_value=None)
        action = TableAction(
            "del", "Delete", handler,
            requires_selection=True, confirm="Sure?",
        )
        table = ActionTable(SAMPLE_DATA, name="test", actions=(action,))
        request = _make_request(
            rf,
            post_params={
                ACTION_SUBMIT_PARAM: "1",
                ACTION_PARAM: "del",
                SELECTION_PARAM: ["1", "2", "3", "4", "5"],
            },
        )
        RequestConfig(request, paginate={"per_page": 25}).configure(table)
        response = table_render(
            request,
            "rg_table/bootstrap/table.html",
            {"table": table, "request": request},
        )
        handler.assert_not_called()
        assert response.status_code == 200
        assert "Bulk operation" in table.empty_selection_message

    def test_bulk_guard_allows_partial_selection(self, rf):
        """Confirmed action on a subset of visible rows is allowed."""
        handler = MagicMock(return_value=None)
        action = TableAction(
            "del", "Delete", handler,
            requires_selection=True, confirm="Sure?",
        )
        table = ActionTable(SAMPLE_DATA, name="test", actions=(action,))
        request = _make_request(
            rf,
            post_params={
                ACTION_SUBMIT_PARAM: "1",
                ACTION_PARAM: "del",
                SELECTION_PARAM: ["1", "3"],
            },
        )
        RequestConfig(request, paginate={"per_page": 25}).configure(table)
        response = table_render(request, "test.html", {"table": table})
        handler.assert_called_once()
        assert response.status_code == 302

    def test_bulk_guard_skipped_without_confirm(self, rf):
        """Actions without confirm field are not guarded."""
        handler = MagicMock(return_value=None)
        action = TableAction("exp", "Export", handler, requires_selection=False)
        table = ActionTable(SAMPLE_DATA, name="test", actions=(action,))
        request = _make_request(
            rf,
            post_params={
                ACTION_SUBMIT_PARAM: "1",
                ACTION_PARAM: "exp",
                SELECTION_PARAM: ["1", "2", "3", "4", "5"],
            },
        )
        RequestConfig(request, paginate={"per_page": 25}).configure(table)
        table_render(request, "test.html", {"table": table})
        handler.assert_called_once()

    def test_empty_selection_message_in_template(self, rf):
        action = TableAction("del", "Delete", _noop_handler, requires_selection=True)
        table = ActionTable(SAMPLE_DATA, name="test", actions=(action,))
        request = _make_request(
            rf,
            post_params={ACTION_SUBMIT_PARAM: "1", ACTION_PARAM: "del"},
        )
        RequestConfig(request, paginate={"per_page": 25}).configure(table)
        response = table_render(
            request,
            "rg_table/bootstrap/table.html",
            {"table": table, "request": request},
        )
        assert "No rows selected" in response.content.decode()


# --- Busy signal and confirms in template ---


class TestActionBarSignals:
    def _render(self, table, rf, kit="bootstrap"):
        request = _make_request(rf)
        RequestConfig(request, paginate={"per_page": 25}).configure(table)
        return render_to_string(
            f"rg_table/{kit}/table.html",
            {"table": table, "request": request},
            request,
        )

    def test_busy_signal_declared(self, rf):
        table = ActionTable(SAMPLE_DATA, name="test")
        html = self._render(table, rf)
        assert "tabletestBusy: false" in html

    def test_confirms_signal_declared(self, rf):
        table = ActionTable(SAMPLE_DATA, name="test")
        html = self._render(table, rf)
        assert "tabletestConfirms:" in html

    def test_go_button_has_click_prevent(self, rf):
        table = ActionTable(SAMPLE_DATA, name="test")
        html = self._render(table, rf)
        assert "data-on:click__prevent" in html
        assert "requestSubmit" in html


# --- Template tag: row_id ---


class TestRowIdTemplateTag:
    def test_row_id_in_rendered_template(self, rf):
        table = ActionTable(SAMPLE_DATA, name="test")
        request = _make_request(rf)
        RequestConfig(request, paginate={"per_page": 25}).configure(table)
        html = render_to_string(
            "rg_table/bootstrap/table_body.html",
            {"table": table, "request": request},
            request,
        )
        # Each row should have a checkbox with value matching the row id
        for item in SAMPLE_DATA:
            assert f'value="{item["id"]}"' in html
