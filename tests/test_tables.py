"""Tests for Table4."""

from rg.table4 import Table4


class SimpleTable(Table4):
    class Meta:
        template_kit = "bootstrap"


def test_table_creation():
    data = [{"name": "Test"}]
    table = SimpleTable(data)
    assert table is not None


def test_template_name_bootstrap():
    table = SimpleTable([])
    assert "bootstrap" in table.template_name
