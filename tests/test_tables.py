"""Tests for Table4 class."""

import django_tables2 as tables

from rg.table4 import Table4, Table4Meta


class SimpleTable(Table4):
    """Simple test table."""

    id = tables.Column()
    name = tables.Column()

    class Meta:
        template_kit = "bootstrap"


class TestTable4Creation:
    """Tests for Table4 instantiation."""

    def test_table_creation_with_data(self, sample_data):
        """Table can be created with data."""
        table = SimpleTable(sample_data)
        assert table is not None
        assert len(list(table.rows)) == 5

    def test_table_creation_empty_data(self):
        """Table can be created with empty data."""
        table = SimpleTable([])
        assert table is not None
        assert len(list(table.rows)) == 0

    def test_table_has_columns(self, sample_data):
        """Table has expected columns."""
        table = SimpleTable(sample_data)
        column_names = [col.name for col in table.columns]
        assert "id" in column_names
        assert "name" in column_names


class TestTemplateKitSelection:
    """Tests for template_kit selection logic."""

    def test_default_template_kit_bootstrap(self, sample_data):
        """Default template_kit is bootstrap."""
        table = SimpleTable(sample_data)
        assert "bootstrap" in table.template_name

    def test_meta_template_kit_bootstrap(self, sample_data):
        """Meta template_kit is respected."""

        class BootstrapTable(Table4):
            class Meta:
                template_kit = "bootstrap"

        table = BootstrapTable(sample_data)
        assert "bootstrap" in table.template_name

    def test_meta_template_kit_bulma(self, sample_data):
        """Meta template_kit bulma is respected."""

        class BulmaTable(Table4):
            class Meta:
                template_kit = "bulma"

        table = BulmaTable(sample_data)
        assert "bulma" in table.template_name

    def test_constructor_template_kit_overrides_meta(self, sample_data):
        """Constructor template_kit overrides Meta."""

        class BootstrapTable(Table4):
            class Meta:
                template_kit = "bootstrap"

        table = BootstrapTable(sample_data, template_kit="bulma")
        assert "bulma" in table.template_name

    def test_constructor_template_name_overrides_kit(self, sample_data):
        """Constructor template_name overrides template_kit."""
        custom_template = "custom/my_table.html"
        table = SimpleTable(sample_data, template_name=custom_template)
        assert table.template_name == custom_template

    def test_template_name_format(self, sample_data):
        """Template name follows expected format."""

        class FreshTable(Table4):
            class Meta:
                template_kit = "bootstrap"

        table = FreshTable(sample_data)
        assert table.template_name == "rg_table4/bootstrap/table.html"


class TestTableName:
    """Tests for table name (for Datastar signals)."""

    def test_table_name_default_empty(self, sample_data):
        """Table name defaults to empty string."""
        table = SimpleTable(sample_data)
        assert table.table_name == ""

    def test_table_name_constructor(self, sample_data):
        """Table name can be set via constructor."""
        table = SimpleTable(sample_data, name="my_table")
        assert table.table_name == "my_table"

    def test_table_name_used_in_template_context(self, sample_data):
        """Table name is accessible for template rendering."""
        table = SimpleTable(sample_data, name="users")
        assert table.table_name == "users"


class TestMetaOptions:
    """Tests for Table4Meta options."""

    def test_enable_filters_default_false(self):
        """enable_filters defaults to False."""

        class TestTable(Table4):
            class Meta:
                template_kit = "bootstrap"

        assert not getattr(TestTable.Meta, "enable_filters", False)

    def test_enable_sorting_default_true(self):
        """enable_sorting defaults to True."""

        class TestTable(Table4):
            class Meta:
                template_kit = "bootstrap"

        assert getattr(TestTable.Meta, "enable_sorting", True)

    def test_infinite_scroll_default_false(self):
        """infinite_scroll defaults to False."""

        class TestTable(Table4):
            class Meta:
                template_kit = "bootstrap"

        assert not getattr(TestTable.Meta, "infinite_scroll", False)

    def test_infinite_scroll_can_be_enabled(self):
        """infinite_scroll can be enabled."""

        class InfiniteTable(Table4):
            class Meta:
                template_kit = "bootstrap"
                infinite_scroll = True

        assert InfiniteTable.Meta.infinite_scroll is True


class TestFiltersetIntegration:
    """Tests for filterset integration."""

    def test_filterset_default_none(self, sample_data):
        """Filterset defaults to None."""
        table = SimpleTable(sample_data)
        assert table.filterset is None

    def test_filterset_can_be_set(self, sample_data):
        """Filterset can be set via kwargs."""
        mock_filterset = object()
        table = SimpleTable(sample_data, filterset=mock_filterset)
        assert table.filterset is mock_filterset


class TestTable4Meta:
    """Tests for Table4Meta class."""

    def test_meta_class_exists(self):
        """Table4Meta class is importable."""
        assert Table4Meta is not None

    def test_meta_can_be_inherited(self):
        """Table4Meta can be inherited."""

        class MyMeta(Table4Meta):
            template_kit = "bulma"
            custom_option = True

        assert MyMeta.template_kit == "bulma"
        assert MyMeta.custom_option is True
