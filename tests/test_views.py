"""Tests for view helpers."""

import django_tables2 as tables
import pytest
from datastar_py.django import DatastarResponse
from django.http import HttpResponse

from rg.table import RequestConfig, Table, table_render


class ViewTable(Table):
    """Table for view tests."""

    id = tables.Column()
    name = tables.Column()

    class Meta:
        template_kit = "bootstrap"


@pytest.fixture
def configured_table(sample_data, get_request):
    """Table configured with RequestConfig."""
    table = ViewTable(sample_data, name="test")
    RequestConfig(get_request, paginate={"per_page": 10}).configure(table)
    return table


@pytest.fixture
def configured_table_datastar(sample_data, datastar_request):
    """Table configured for Datastar request."""
    table = ViewTable(sample_data, name="test")
    RequestConfig(datastar_request, paginate={"per_page": 10}).configure(table)
    return table


class TestTableRenderRegular:
    """Tests for table_render with regular requests."""

    def test_returns_http_response(self, get_request, configured_table):
        """Regular request returns HttpResponse."""
        response = table_render(
            get_request,
            "rg_table/bootstrap/table.html",
            {"table": configured_table},
        )
        assert isinstance(response, HttpResponse)
        assert not isinstance(response, DatastarResponse)

    def test_response_contains_table_html(self, get_request, configured_table):
        """Response contains rendered table HTML."""
        response = table_render(
            get_request,
            "rg_table/bootstrap/table.html",
            {"table": configured_table},
        )
        content = response.content.decode("utf-8")
        assert "<table" in content


class TestTableRenderDatastar:
    """Tests for table_render with Datastar requests."""

    def test_returns_datastar_response(self, datastar_request, configured_table_datastar):
        """Datastar request returns DatastarResponse."""
        response = table_render(
            datastar_request,
            "rg_table/bootstrap/table.html",
            {"table": configured_table_datastar},
        )
        assert isinstance(response, DatastarResponse)

    def test_datastar_response_is_streaming(self, datastar_request, configured_table_datastar):
        """DatastarResponse is a streaming response."""
        response = table_render(
            datastar_request,
            "rg_table/bootstrap/table.html",
            {"table": configured_table_datastar},
        )
        assert response.streaming is True

    def test_datastar_content_type(self, datastar_request, configured_table_datastar):
        """DatastarResponse has correct content type."""
        response = table_render(
            datastar_request,
            "rg_table/bootstrap/table.html",
            {"table": configured_table_datastar},
        )
        assert "text/event-stream" in response["Content-Type"]


class TestTableRenderContext:
    """Tests for context handling in table_render."""

    def test_extra_context_passed(self, get_request, configured_table):
        """Extra context is passed to template."""
        response = table_render(
            get_request,
            "rg_table/bootstrap/table.html",
            {
                "table": configured_table,
                "extra_var": "test_value",
            },
        )
        # Response should render without error
        assert response.status_code == 200

    def test_table_in_params_required(self, get_request):
        """table must be in params."""
        with pytest.raises(KeyError):
            table_render(get_request, "rg_table/bootstrap/table.html", {})


class TestDatastarRequestDetection:
    """Tests for Datastar request detection."""

    def test_detects_datastar_header(self, request_factory, sample_data):
        """Datastar-Request header is detected."""
        request = request_factory.get("/", HTTP_DATASTAR_REQUEST="true")
        table = ViewTable(sample_data, name="test")
        RequestConfig(request, paginate={"per_page": 10}).configure(table)

        response = table_render(
            request,
            "rg_table/bootstrap/table.html",
            {"table": table},
        )
        assert isinstance(response, DatastarResponse)

    def test_no_datastar_header(self, request_factory, sample_data):
        """No Datastar header means regular response."""
        request = request_factory.get("/")
        table = ViewTable(sample_data, name="test")
        RequestConfig(request, paginate={"per_page": 10}).configure(table)

        response = table_render(
            request,
            "rg_table/bootstrap/table.html",
            {"table": table},
        )
        assert isinstance(response, HttpResponse)
        assert not isinstance(response, DatastarResponse)

    def test_datastar_header_case_sensitive(self, request_factory, sample_data):
        """Datastar-Request header value must be 'true'."""
        request = request_factory.get("/", HTTP_DATASTAR_REQUEST="false")
        table = ViewTable(sample_data, name="test")
        RequestConfig(request, paginate={"per_page": 10}).configure(table)

        response = table_render(
            request,
            "rg_table/bootstrap/table.html",
            {"table": table},
        )
        # Should be regular response since header is not 'true'
        assert not isinstance(response, DatastarResponse)
