"""Tests for DynamicColumn class."""

import django_tables2 as tables

from rg.table4 import DynamicColumn, Table4


class BaseTable(Table4):
    """Base table for dynamic column tests."""

    id = tables.Column()
    name = tables.Column()

    class Meta:
        template_kit = "bootstrap"


class TestDynamicColumnCreation:
    """Tests for DynamicColumn instantiation."""

    def test_dynamic_column_creation(self):
        """DynamicColumn can be created."""
        col = DynamicColumn(name="custom")
        assert col is not None
        assert col.dynamic_name == "custom"

    def test_dynamic_column_with_accessor(self):
        """DynamicColumn can have accessor."""
        col = DynamicColumn(name="custom", accessor="get_custom")
        assert col.dynamic_name == "custom"

    def test_dynamic_column_inherits_from_tables_column(self):
        """DynamicColumn inherits from django_tables2.Column."""
        col = DynamicColumn(name="test")
        assert isinstance(col, tables.Column)


class TestDynamicColumnWithTable:
    """Tests for DynamicColumn used with Table4."""

    def test_extra_columns_with_dynamic_column(self, sample_data):
        """Table can use DynamicColumn via extra_columns."""
        extra = [("custom", DynamicColumn(name="custom", accessor="country"))]
        table = BaseTable(sample_data, extra_columns=extra)

        column_names = [col.name for col in table.columns]
        assert "custom" in column_names

    def test_dynamic_column_renders_data(self, sample_data):
        """DynamicColumn renders data correctly."""
        extra = [("custom", DynamicColumn(name="custom", accessor="country"))]
        table = BaseTable(sample_data, extra_columns=extra)

        # Get first row's custom column value
        first_row = list(table.rows)[0]
        # Find the custom column value
        custom_col = None
        for col, cell in first_row.items():
            if col.name == "custom":
                custom_col = cell
                break

        assert custom_col is not None

    def test_multiple_dynamic_columns(self, sample_data):
        """Table can have multiple dynamic columns."""
        extra = [
            ("col1", DynamicColumn(name="col1", accessor="country")),
            ("col2", DynamicColumn(name="col2", accessor="population")),
        ]
        table = BaseTable(sample_data, extra_columns=extra)

        column_names = [col.name for col in table.columns]
        assert "col1" in column_names
        assert "col2" in column_names


class TestDynamicColumnOptions:
    """Tests for DynamicColumn options."""

    def test_verbose_name(self, sample_data):
        """DynamicColumn supports verbose_name."""
        extra = [
            (
                "custom",
                DynamicColumn(name="custom", accessor="country", verbose_name="Country Name"),
            )
        ]
        table = BaseTable(sample_data, extra_columns=extra)

        for col in table.columns:
            if col.name == "custom":
                assert col.verbose_name == "Country Name"
                break

    def test_orderable(self, sample_data):
        """DynamicColumn supports orderable option."""
        extra = [("custom", DynamicColumn(name="custom", accessor="country", orderable=True))]
        table = BaseTable(sample_data, extra_columns=extra)

        for col in table.columns:
            if col.name == "custom":
                assert col.orderable is True
                break

    def test_visible(self, sample_data):
        """DynamicColumn supports visible option."""
        extra = [("hidden", DynamicColumn(name="hidden", accessor="country", visible=False))]
        table = BaseTable(sample_data, extra_columns=extra)

        visible_names = [col.name for col in table.columns]
        # Hidden columns should not appear in visible columns
        assert "hidden" not in visible_names
