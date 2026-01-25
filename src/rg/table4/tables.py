"""Extended table classes with Datastar and filter integration."""

import importlib.util
from typing import Any

import django_tables2 as tables

HAS_FILTERS = importlib.util.find_spec("django_filters") is not None


class Table4Meta:
    """
    Meta options for Table4.

    Attributes:
        template_name: Template to use (auto-detected from template_kit)
        template_kit: CSS template_kit ('bootstrap' or 'bulma')
        filterset_class: django-filter FilterSet class (optional)
        enable_filters: Enable django-filter integration (default: False)
        enable_sorting: Enable column sorting (default: True)
    """

    pass


class Table4(tables.Table):
    """
    Extended django-tables2 Table with Datastar and filter support.

    Example:
        class MyTable(Table4):
            name = tables.Column()

            class Meta(Table4Meta):
                template_kit = 'bootstrap'
                enable_filters = True
                filterset_class = MyFilterSet
    """

    class Meta(Table4Meta):
        template_kit = "bootstrap"
        enable_filters = False
        enable_sorting = True

    def __init__(
        self,
        *args: Any,
        template_kit: str | None = None,
        name: str = "",
        **kwargs: Any,
    ) -> None:
        # Extract filter-related kwargs
        self.filterset = kwargs.pop("filterset", None)
        self.table_name = name  # For Datastar signals like table_<name>
        explicit_kit = template_kit is not None
        super().__init__(*args, **kwargs)

        # Setup template based on template_kit
        # Priority: kwarg > Meta.template_kit > settings.TABLE4_DEFAULT_TEMPLATE_KIT > "bootstrap"
        from django.conf import settings

        if template_kit is None:
            default_kit = getattr(settings, "TABLE4_DEFAULT_TEMPLATE_KIT", "bootstrap")
            template_kit = getattr(self.Meta, "template_kit", None) or default_kit

        # Set template if: explicit kwarg passed, or template not yet set, or still default
        if explicit_kit or not getattr(self._meta, "template_name", None) or self._meta.template_name == "django_tables2/table.html":
            self._meta.template_name = f"rg_table4/{template_kit}/table.html"

