"""Tests for template rendering."""

import django_tables2 as tables
import pytest
from django.template.loader import get_template, render_to_string

from rg.table import RequestConfig, Table


class TemplateTable(Table):
    """Table for template tests."""

    id = tables.Column()
    name = tables.Column()
    country = tables.Column()

    class Meta:
        template_kit = "bootstrap"


@pytest.fixture
def table_with_request(sample_data, get_request):
    """Table with request configured."""
    table = TemplateTable(sample_data, name="test")
    RequestConfig(get_request, paginate={"per_page": 10}).configure(table)
    return table


class TestTemplateExists:
    """Tests that templates exist and can be loaded."""

    @pytest.mark.parametrize(
        "template_path",
        [
            "rg_table/bootstrap/table.html",
            "rg_table/bootstrap/table_body.html",
            "rg_table/bootstrap/paginator_simple.html",
            "rg_table/bootstrap/table_filtered.html",
            "rg_table/bootstrap/table_infinite.html",
            "rg_table/bootstrap/paginator_infinite.html",
        ],
    )
    def test_bootstrap_templates_exist(self, template_path):
        """Bootstrap templates can be loaded."""
        template = get_template(template_path)
        assert template is not None

    @pytest.mark.parametrize(
        "template_path",
        [
            "rg_table/bulma/table.html",
            "rg_table/bulma/table_body.html",
            "rg_table/bulma/paginator_simple.html",
            "rg_table/bulma/table_filtered.html",
            "rg_table/bulma/table_infinite.html",
            "rg_table/bulma/paginator_infinite.html",
        ],
    )
    def test_bulma_templates_exist(self, template_path):
        """Bulma templates can be loaded."""
        template = get_template(template_path)
        assert template is not None


class TestBootstrapTemplateRendering:
    """Tests for Bootstrap template rendering."""

    def test_table_renders(self, table_with_request, get_request):
        """Bootstrap table template renders."""
        html = render_to_string(
            "rg_table/bootstrap/table.html",
            {"table": table_with_request},
            get_request,
        )
        assert "<table" in html
        assert "table-striped" in html  # Bootstrap class

    def test_table_contains_data(self, table_with_request, get_request):
        """Rendered table contains data."""
        html = render_to_string(
            "rg_table/bootstrap/table.html",
            {"table": table_with_request},
            get_request,
        )
        assert "Alice" in html  # From sample_data
        assert "USA" in html

    def test_table_has_headers(self, table_with_request, get_request):
        """Rendered table has column headers."""
        html = render_to_string(
            "rg_table/bootstrap/table.html",
            {"table": table_with_request},
            get_request,
        )
        assert "<th" in html
        assert "Id" in html or "id" in html.lower()
        assert "Name" in html or "name" in html.lower()

    def test_pagination_renders(self, sample_data, get_request):
        """Pagination renders when multiple pages."""
        # Create table with enough data for pagination
        large_data = [{"id": i, "name": f"Name {i}", "country": "US"} for i in range(50)]
        table = TemplateTable(large_data, name="test")
        RequestConfig(get_request, paginate={"per_page": 10}).configure(table)

        html = render_to_string(
            "rg_table/bootstrap/table.html",
            {"table": table},
            get_request,
        )
        assert "pagination" in html


class TestBulmaTemplateRendering:
    """Tests for Bulma template rendering."""

    def test_table_renders(self, sample_data, get_request):
        """Bulma table template renders."""

        class BulmaTable(Table):
            id = tables.Column()
            name = tables.Column()

            class Meta:
                template_kit = "bulma"

        table = BulmaTable(sample_data, name="test")
        RequestConfig(get_request, paginate={"per_page": 10}).configure(table)

        html = render_to_string(
            "rg_table/bulma/table.html",
            {"table": table},
            get_request,
        )
        assert "<table" in html
        assert "is-striped" in html  # Bulma class

    def test_table_contains_data(self, sample_data, get_request):
        """Rendered Bulma table contains data."""

        class BulmaTable(Table):
            id = tables.Column()
            name = tables.Column()
            country = tables.Column()

            class Meta:
                template_kit = "bulma"

        table = BulmaTable(sample_data, name="test")
        RequestConfig(get_request, paginate={"per_page": 10}).configure(table)

        html = render_to_string(
            "rg_table/bulma/table.html",
            {"table": table},
            get_request,
        )
        assert "Alice" in html
        assert "USA" in html


class TestInfiniteScrollTemplate:
    """Tests for infinite scroll template."""

    def test_infinite_template_renders(self, sample_data, get_request):
        """Infinite scroll template renders."""
        table = TemplateTable(sample_data, name="infinite")
        RequestConfig(get_request, paginate={"per_page": 3}).configure(table)

        html = render_to_string(
            "rg_table/bootstrap/table_infinite.html",
            {"table": table},
            get_request,
        )
        assert "<table" in html

    def test_infinite_has_scroll_trigger(self, get_request):
        """Infinite template has scroll trigger when more pages."""
        large_data = [{"id": i, "name": f"Name {i}", "country": "US"} for i in range(50)]
        table = TemplateTable(large_data, name="infinite")
        RequestConfig(get_request, paginate={"per_page": 10}).configure(table)

        html = render_to_string(
            "rg_table/bootstrap/table_infinite.html",
            {"table": table},
            get_request,
        )
        assert "scroll_trigger" in html
        assert "data-on-intersect" in html


class TestTableName:
    """Tests for table_name in templates."""

    def test_table_name_in_wrapper_id(self, table_with_request, get_request):
        """Table name appears in wrapper div id."""
        html = render_to_string(
            "rg_table/bootstrap/table.html",
            {"table": table_with_request},
            get_request,
        )
        assert 'id="table_test_inner"' in html

    def test_empty_table_name_in_wrapper_id(self, sample_data, get_request):
        """Empty table name still creates valid id."""
        table = TemplateTable(sample_data, name="")
        RequestConfig(get_request, paginate={"per_page": 10}).configure(table)

        html = render_to_string(
            "rg_table/bootstrap/table.html",
            {"table": table},
            get_request,
        )
        assert 'id="table__inner"' in html


class TestEmptyTable:
    """Tests for empty table rendering."""

    def test_empty_table_renders(self, get_request):
        """Empty table renders with message."""
        table = TemplateTable([], name="empty")
        RequestConfig(get_request, paginate={"per_page": 10}).configure(table)

        html = render_to_string(
            "rg_table/bootstrap/table.html",
            {"table": table},
            get_request,
        )
        assert "No data available" in html or "empty" in html.lower()
