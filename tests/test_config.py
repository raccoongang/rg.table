"""Tests for RequestConfig class."""

import django_tables2 as tables

from rg.table import RequestConfig, Table


class PaginatedTable(Table):
    """Table for pagination tests."""

    id = tables.Column()
    name = tables.Column()
    value = tables.Column()

    class Meta:
        template_kit = "bootstrap"


class TestRequestConfigBasic:
    """Basic RequestConfig tests."""

    def test_configure_returns_table(self, get_request, large_data):
        """configure() returns the table."""
        table = PaginatedTable(large_data)
        config = RequestConfig(get_request)
        result = config.configure(table)
        assert result is table

    def test_request_attached_to_table(self, get_request, large_data):
        """Request is attached to table."""
        table = PaginatedTable(large_data)
        config = RequestConfig(get_request)
        config.configure(table)
        assert table.request is get_request


class TestPagination:
    """Tests for pagination configuration."""

    def test_default_pagination_enabled(self, get_request, large_data):
        """Pagination is enabled by default."""
        table = PaginatedTable(large_data)
        config = RequestConfig(get_request)
        config.configure(table)
        assert table.page is not None

    def test_pagination_disabled(self, get_request, large_data):
        """Pagination can be disabled."""
        table = PaginatedTable(large_data)
        config = RequestConfig(get_request, paginate=False)
        config.configure(table)
        assert not hasattr(table, "page") or table.page is None

    def test_per_page_setting(self, get_request, large_data):
        """per_page can be configured."""
        table = PaginatedTable(large_data)
        config = RequestConfig(get_request, paginate={"per_page": 10})
        config.configure(table)
        assert table.paginator.per_page == 10

    def test_per_page_from_request(self, request_factory, large_data):
        """per_page can come from request."""
        request = request_factory.get("/", {"per_page": "25"})
        table = PaginatedTable(large_data)
        config = RequestConfig(request, paginate={"per_page": 10})
        config.configure(table)
        assert table.paginator.per_page == 25

    def test_page_from_request(self, request_factory, large_data):
        """page can come from request."""
        request = request_factory.get("/", {"page": "2"})
        table = PaginatedTable(large_data)
        config = RequestConfig(request, paginate={"per_page": 10})
        config.configure(table)
        assert table.page.number == 2

    def test_invalid_page_shows_first(self, request_factory, large_data):
        """Invalid page number shows first page (silent mode)."""
        request = request_factory.get("/", {"page": "invalid"})
        table = PaginatedTable(large_data)
        config = RequestConfig(request, paginate={"per_page": 10})
        config.configure(table)
        assert table.page.number == 1

    def test_empty_page_shows_last(self, request_factory, large_data):
        """Empty page (too high) shows last page (silent mode)."""
        request = request_factory.get("/", {"page": "9999"})
        table = PaginatedTable(large_data)
        config = RequestConfig(request, paginate={"per_page": 10})
        config.configure(table)
        # Should be on the last page
        assert table.page.number == table.paginator.num_pages


class TestSorting:
    """Tests for sorting configuration."""

    def test_order_by_from_request(self, request_factory, large_data):
        """order_by can come from request."""
        request = request_factory.get("/", {"sort": "name"})
        table = PaginatedTable(large_data)
        config = RequestConfig(request, paginate={"per_page": 10})
        config.configure(table)
        assert table.order_by == ("name",)

    def test_order_by_descending(self, request_factory, large_data):
        """Descending order_by works."""
        request = request_factory.get("/", {"sort": "-value"})
        table = PaginatedTable(large_data)
        config = RequestConfig(request, paginate={"per_page": 10})
        config.configure(table)
        assert table.order_by == ("-value",)

    def test_multiple_order_by(self, request_factory, large_data):
        """Multiple order_by columns work."""
        request = request_factory.get("/", {"sort": ["name", "-value"]})
        table = PaginatedTable(large_data)
        config = RequestConfig(request, paginate={"per_page": 10})
        config.configure(table)
        assert table.order_by == ("name", "-value")


class TestPrefixedFields:
    """Tests for prefixed field names."""

    def test_prefixed_page_field(self, request_factory, large_data):
        """Prefixed page field works with table prefix."""

        class PrefixedTable(Table):
            id = tables.Column()

            class Meta:
                template_kit = "bootstrap"

        table = PrefixedTable(large_data, prefix="my_")
        request = request_factory.get("/", {"my_page": "3"})
        config = RequestConfig(request, paginate={"per_page": 10})
        config.configure(table)
        assert table.page.number == 3

    def test_prefixed_per_page_field(self, request_factory, large_data):
        """Prefixed per_page field works with table prefix."""

        class PrefixedTable(Table):
            id = tables.Column()

            class Meta:
                template_kit = "bootstrap"

        table = PrefixedTable(large_data, prefix="my_")
        request = request_factory.get("/", {"my_per_page": "20"})
        config = RequestConfig(request, paginate={"per_page": 10})
        config.configure(table)
        assert table.paginator.per_page == 20
