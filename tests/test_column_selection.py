"""Tests for column selection feature."""

import django_tables2 as tables
import pytest
from django.template.loader import render_to_string
from django.test import RequestFactory

from rg.table import RequestConfig, Table, TableMeta
from rg.table.config import (
    COLUMN_SELECTION_PARAM,
    COLUMN_SELECTION_SUBMIT,
    get_column_preference,
    set_column_preference,
)

# --- Test table classes ---


class ColumnSelectTable(Table):
    """Table with column selection enabled via Meta."""

    id = tables.Column()
    name = tables.Column()
    country = tables.Column()
    population = tables.Column()

    class Meta(TableMeta):
        template_kit = "bootstrap"
        enable_column_selection = True


class PinnedColumnTable(Table):
    """Table with pinned columns."""

    id = tables.Column()
    name = tables.Column()
    country = tables.Column()
    population = tables.Column()

    class Meta(TableMeta):
        template_kit = "bootstrap"
        enable_column_selection = True
        pinned_columns = ("name",)


class NoSelectionTable(Table):
    """Table without column selection (default)."""

    id = tables.Column()
    name = tables.Column()

    class Meta(TableMeta):
        template_kit = "bootstrap"


# --- Fixtures ---


@pytest.fixture
def data():
    return [
        {"id": 1, "name": "Alice", "country": "USA", "population": 1000},
        {"id": 2, "name": "Bob", "country": "UK", "population": 2000},
        {"id": 3, "name": "Charlie", "country": "Canada", "population": 3000},
    ]


@pytest.fixture
def rf():
    return RequestFactory()


def _make_request(rf, get_params=None, post_params=None):
    """Create a request with a session dict attached."""
    if post_params:
        request = rf.post("/", post_params)
    else:
        request = rf.get("/", get_params or {})
    request.session = {}
    return request


def _column_submit_params(*columns):
    """Build POST data simulating form submission with column checkboxes."""
    params = {COLUMN_SELECTION_SUBMIT: "1"}
    if columns:
        params[COLUMN_SELECTION_PARAM] = list(columns)
    return params


# --- Session helper tests ---


class TestSessionHelpers:
    def test_get_column_preference_returns_none_when_unset(self):
        session = {}
        assert get_column_preference(session, "mytable") is None

    def test_set_and_get_column_preference(self):
        session = {}
        set_column_preference(session, "mytable", ["id", "name"])
        assert get_column_preference(session, "mytable") == ["id", "name"]

    def test_separate_tables_have_separate_preferences(self):
        session = {}
        set_column_preference(session, "table_a", ["id"])
        set_column_preference(session, "table_b", ["name", "country"])
        assert get_column_preference(session, "table_a") == ["id"]
        assert get_column_preference(session, "table_b") == ["name", "country"]


# --- Meta/init tests ---


class TestColumnSelectionMeta:
    def test_disabled_by_default(self, data):
        table = NoSelectionTable(data)
        assert table.enable_column_selection is False

    def test_enabled_via_meta(self, data):
        table = ColumnSelectTable(data, name="test")
        assert table.enable_column_selection is True

    def test_enabled_via_kwarg(self, data):
        table = NoSelectionTable(data, name="test", enable_column_selection=True)
        assert table.enable_column_selection is True

    def test_kwarg_overrides_meta(self, data):
        table = ColumnSelectTable(data, name="test", enable_column_selection=False)
        assert table.enable_column_selection is False

    def test_pinned_columns_from_meta(self, data):
        table = PinnedColumnTable(data, name="test")
        assert table.pinned_columns == ("name",)

    def test_pinned_columns_default_empty(self, data):
        table = ColumnSelectTable(data, name="test")
        assert table.pinned_columns == ()

    def test_all_columns_meta_empty_before_configure(self, data):
        table = ColumnSelectTable(data, name="test")
        assert table.all_columns_meta == []


# --- RequestConfig column selection tests ---


class TestColumnSelection:
    def test_first_visit_all_columns_visible(self, rf, data):
        """First visit with no session and no param: all columns shown."""
        request = _make_request(rf)
        table = ColumnSelectTable(data, name="test")
        RequestConfig(request, paginate=False).configure(table)

        visible = [col.name for col in table.columns]
        assert visible == ["id", "name", "country", "population"]

    def test_form_submit_stores_in_session(self, rf, data):
        """Form submission saves preference to session."""
        request = _make_request(rf, post_params=_column_submit_params("id", "name"))
        table = ColumnSelectTable(data, name="test")
        RequestConfig(request, paginate=False).configure(table)

        assert get_column_preference(request.session, "test") == ["id", "name"]

    def test_form_submit_hides_unselected(self, rf, data):
        """Form submission hides columns not in the list."""
        request = _make_request(rf, post_params=_column_submit_params("id", "name"))
        table = ColumnSelectTable(data, name="test")
        RequestConfig(request, paginate=False).configure(table)

        visible = [col.name for col in table.columns]
        assert visible == ["id", "name"]

    def test_columns_read_from_session(self, rf, data):
        """Stored session preference is applied when no form submission."""
        request = _make_request(rf)
        set_column_preference(request.session, "test", ["name", "country"])
        table = ColumnSelectTable(data, name="test")
        RequestConfig(request, paginate=False).configure(table)

        visible = [col.name for col in table.columns]
        assert visible == ["name", "country"]

    def test_invalid_column_names_ignored(self, rf, data):
        """Unknown column names in form submission are silently dropped."""
        request = _make_request(rf, post_params=_column_submit_params("id", "nonexistent", "name"))
        table = ColumnSelectTable(data, name="test")
        RequestConfig(request, paginate=False).configure(table)

        visible = [col.name for col in table.columns]
        assert visible == ["id", "name"]

    def test_stale_session_columns_filtered(self, rf, data):
        """Session columns that no longer exist in the table are filtered out."""
        request = _make_request(rf)
        set_column_preference(request.session, "test", ["id", "removed_col", "name"])
        table = ColumnSelectTable(data, name="test")
        RequestConfig(request, paginate=False).configure(table)

        visible = [col.name for col in table.columns]
        assert visible == ["id", "name"]

    def test_no_selection_without_table_name(self, rf, data):
        """Column selection is skipped when table has no name."""
        request = _make_request(rf, post_params=_column_submit_params("id"))
        table = ColumnSelectTable(data)  # no name
        RequestConfig(request, paginate=False).configure(table)

        # All columns remain visible (selection was skipped)
        visible = [col.name for col in table.columns]
        assert visible == ["id", "name", "country", "population"]

    def test_no_selection_when_disabled(self, rf, data):
        """Column selection is skipped when enable_column_selection=False."""
        request = _make_request(rf, post_params=_column_submit_params("id"))
        table = NoSelectionTable(data, name="test")
        RequestConfig(request, paginate=False).configure(table)

        visible = [col.name for col in table.columns]
        assert visible == ["id", "name"]

    def test_bare_columns_param_without_sentinel_ignored(self, rf, data):
        """_columns param without _columns_submit sentinel uses session."""
        request = _make_request(rf, get_params={COLUMN_SELECTION_PARAM: ["id"]})
        set_column_preference(request.session, "test", ["name", "country"])
        table = ColumnSelectTable(data, name="test")
        RequestConfig(request, paginate=False).configure(table)

        # Should use session, not the bare _columns param
        visible = [col.name for col in table.columns]
        assert visible == ["name", "country"]


# --- Pinned columns tests ---


class TestPinnedColumns:
    def test_pinned_always_visible(self, rf, data):
        """Pinned column is always visible even if omitted from form."""
        request = _make_request(rf, post_params=_column_submit_params("id", "country"))
        table = PinnedColumnTable(data, name="test")
        RequestConfig(request, paginate=False).configure(table)

        visible = [col.name for col in table.columns]
        assert "name" in visible  # pinned
        assert "id" in visible
        assert "country" in visible

    def test_pinned_enforced_from_session(self, rf, data):
        """Pinned column is enforced even when reading from session."""
        request = _make_request(rf)
        set_column_preference(request.session, "test", ["id", "population"])
        table = PinnedColumnTable(data, name="test")
        RequestConfig(request, paginate=False).configure(table)

        visible = [col.name for col in table.columns]
        assert "name" in visible  # pinned, added back

    def test_pinned_marked_in_all_columns_meta(self, rf, data):
        """Pinned columns are marked as pinned in all_columns_meta."""
        request = _make_request(rf)
        table = PinnedColumnTable(data, name="test")
        RequestConfig(request, paginate=False).configure(table)

        meta_by_name = {m["name"]: m for m in table.all_columns_meta}
        assert meta_by_name["name"]["pinned"] is True
        assert meta_by_name["id"]["pinned"] is False


# --- Minimum visibility tests ---


class TestMinimumVisibility:
    def test_empty_form_submit_shows_first(self, rf, data):
        """Form submitted with no checkboxes shows at least the first column."""
        request = _make_request(rf, post_params={COLUMN_SELECTION_SUBMIT: "1"})
        table = ColumnSelectTable(data, name="test")
        RequestConfig(request, paginate=False).configure(table)

        visible = [col.name for col in table.columns]
        assert len(visible) >= 1

    def test_all_invalid_columns_shows_first(self, rf, data):
        """If all submitted names are invalid, show the first column."""
        request = _make_request(
            rf, post_params=_column_submit_params("bogus1", "bogus2")
        )
        table = ColumnSelectTable(data, name="test")
        RequestConfig(request, paginate=False).configure(table)

        visible = [col.name for col in table.columns]
        assert visible == ["id"]  # first column as fallback


# --- all_columns_meta tests ---


class TestAllColumnsMeta:
    def test_contains_all_columns(self, rf, data):
        """all_columns_meta contains metadata for all columns."""
        request = _make_request(rf, post_params=_column_submit_params("id", "name"))
        table = ColumnSelectTable(data, name="test")
        RequestConfig(request, paginate=False).configure(table)

        names = [m["name"] for m in table.all_columns_meta]
        assert names == ["id", "name", "country", "population"]

    def test_visible_flag_reflects_selection(self, rf, data):
        """all_columns_meta visible flag matches actual visibility."""
        request = _make_request(rf, post_params=_column_submit_params("id", "country"))
        table = ColumnSelectTable(data, name="test")
        RequestConfig(request, paginate=False).configure(table)

        meta_by_name = {m["name"]: m for m in table.all_columns_meta}
        assert meta_by_name["id"]["visible"] is True
        assert meta_by_name["name"]["visible"] is False
        assert meta_by_name["country"]["visible"] is True
        assert meta_by_name["population"]["visible"] is False

    def test_has_header_field(self, rf, data):
        """all_columns_meta entries have a header field."""
        request = _make_request(rf)
        table = ColumnSelectTable(data, name="test")
        RequestConfig(request, paginate=False).configure(table)

        for meta in table.all_columns_meta:
            assert "header" in meta
            assert isinstance(meta["header"], str)
            assert len(meta["header"]) > 0


# --- Template rendering tests ---


class TestColumnSelectorTemplate:
    def test_selector_rendered_when_enabled(self, rf, data):
        """Column selector appears in rendered output when enabled."""
        request = _make_request(rf)
        table = ColumnSelectTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 10}).configure(table)

        html = render_to_string(
            table._meta.template_name,
            {"table": table, "request": request},
            request=request,
        )
        assert 'id="col_sel_test"' in html
        assert "Columns" in html

    def test_selector_not_rendered_when_disabled(self, rf, data):
        """Column selector does not appear when feature is disabled."""
        request = _make_request(rf)
        table = NoSelectionTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 10}).configure(table)

        html = render_to_string(
            table._meta.template_name,
            {"table": table, "request": request},
            request=request,
        )
        assert "col_sel_" not in html

    def test_selector_checkboxes_match_columns(self, rf, data):
        """One checkbox per column in the selector."""
        request = _make_request(rf)
        table = ColumnSelectTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 10}).configure(table)

        html = render_to_string(
            table._meta.template_name,
            {"table": table, "request": request},
            request=request,
        )
        for col_meta in table.all_columns_meta:
            assert f'value="{col_meta["name"]}"' in html

    def test_selector_has_apply_button(self, rf, data):
        """Column selector has an Apply submit button."""
        request = _make_request(rf)
        table = ColumnSelectTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 10}).configure(table)

        html = render_to_string(
            table._meta.template_name,
            {"table": table, "request": request},
            request=request,
        )
        assert "Apply" in html
        assert "contentType" in html

    def test_selector_has_hidden_sentinel(self, rf, data):
        """Column selector form includes _columns_submit hidden input."""
        request = _make_request(rf)
        table = ColumnSelectTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 10}).configure(table)

        html = render_to_string(
            table._meta.template_name,
            {"table": table, "request": request},
            request=request,
        )
        assert '_columns_submit' in html

    def test_hidden_columns_not_in_table_headers(self, rf, data):
        """Hidden columns do not appear in table headers."""
        request = _make_request(rf, post_params=_column_submit_params("id", "name"))
        table = ColumnSelectTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 10}).configure(table)

        html = render_to_string(
            "rg_table/bootstrap/table_body.html",
            {"table": table, "request": request},
            request=request,
        )
        assert "<th" in html
        # "Country" and "Population" headers should not be in the table body
        assert ">Country<" not in html
        assert ">Population<" not in html

    def test_pinned_column_has_hidden_input(self, rf, data):
        """Pinned columns get a hidden input to ensure they're always submitted."""
        request = _make_request(rf)
        table = PinnedColumnTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 10}).configure(table)

        html = render_to_string(
            table._meta.template_name,
            {"table": table, "request": request},
            request=request,
        )
        assert 'type="hidden" name="_columns" value="name"' in html
