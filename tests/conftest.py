"""Pytest configuration and shared fixtures for rg.table tests."""

import django
import os

# Configure Django settings before any Django imports
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
django.setup()

import django_tables2 as tables
import pytest
from django.test import RequestFactory

from rg.table import Table


# Sample data for testing
@pytest.fixture
def sample_data():
    """Sample data for table tests."""
    return [
        {"id": 1, "name": "Alice", "country": "USA", "population": 1000},
        {"id": 2, "name": "Bob", "country": "UK", "population": 2000},
        {"id": 3, "name": "Charlie", "country": "Canada", "population": 3000},
        {"id": 4, "name": "Diana", "country": "Australia", "population": 4000},
        {"id": 5, "name": "Eve", "country": "Germany", "population": 5000},
    ]


@pytest.fixture
def large_data():
    """Large dataset for pagination tests."""
    return [{"id": i, "name": f"Item {i}", "value": i * 10} for i in range(1, 101)]


@pytest.fixture
def request_factory():
    """Django request factory."""
    return RequestFactory()


@pytest.fixture
def get_request(request_factory):
    """Basic GET request."""
    return request_factory.get("/")


@pytest.fixture
def datastar_request(request_factory):
    """GET request with Datastar header."""
    return request_factory.get("/", HTTP_DATASTAR_REQUEST="true")


# Table classes for testing
class SimpleTable(Table):
    """Simple table with no explicit template_kit."""

    id = tables.Column()
    name = tables.Column()


class BootstrapTable(Table):
    """Table with Bootstrap template_kit."""

    id = tables.Column()
    name = tables.Column()
    country = tables.Column()

    class Meta:
        template_kit = "bootstrap"


class BulmaTable(Table):
    """Table with Bulma template_kit."""

    id = tables.Column()
    name = tables.Column()
    country = tables.Column()

    class Meta:
        template_kit = "bulma"


class SortableTable(Table):
    """Table with sortable columns."""

    id = tables.Column(orderable=True)
    name = tables.Column(orderable=True)
    value = tables.Column(orderable=True)

    class Meta:
        template_kit = "bootstrap"
        orderable = True


class InfiniteScrollTable(Table):
    """Table with infinite scroll enabled."""

    id = tables.Column()
    name = tables.Column()

    class Meta:
        template_kit = "bootstrap"
        infinite_scroll = True


@pytest.fixture
def simple_table(sample_data):
    """Simple table instance."""
    return SimpleTable(sample_data)


@pytest.fixture
def bootstrap_table(sample_data):
    """Bootstrap table instance."""
    return BootstrapTable(sample_data)


@pytest.fixture
def bulma_table(sample_data):
    """Bulma table instance."""
    return BulmaTable(sample_data)


@pytest.fixture
def sortable_table(large_data):
    """Sortable table instance with large dataset."""
    return SortableTable(large_data)
