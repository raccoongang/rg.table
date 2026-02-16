"""Extended table classes with Datastar and filter integration."""

import importlib.util
from typing import Any

import django_tables2 as tables

HAS_FILTERS = importlib.util.find_spec("django_filters") is not None


class TableMeta:
    """
    Meta options for Table.

    Attributes:
        template_name: Template to use (auto-detected from template_kit)
        template_kit: CSS template_kit ('bootstrap' or 'bulma')
        filterset_class: django-filter FilterSet class (optional)
        enable_filters: Enable django-filter integration (default: False)
        enable_sorting: Enable column sorting (default: True)
        infinite_scroll: Enable infinite scroll pagination (default: False)
        enable_column_selection: Enable user column selection (default: False)
        pinned_columns: Columns that cannot be hidden by the user (default: ())
        enable_profiles: Enable named profile save/load (default: False)
        enable_per_page_selection: Enable per-page size selector (default: False)
        per_page_choices: Allowed per-page sizes (default: (10, 25, 50, 100))
    """

    pass


class Table(tables.Table):  # type: ignore[misc]
    """
    Extended django-tables2 Table with Datastar and filter support.

    Example:
        class MyTable(Table):
            name = tables.Column()

            class Meta(TableMeta):
                template_kit = 'bootstrap'
                enable_filters = True
                filterset_class = MyFilterSet
    """

    class Meta(TableMeta):
        template_kit = "bootstrap"
        enable_filters = False
        enable_sorting = True
        infinite_scroll = False
        enable_column_selection = False
        pinned_columns: tuple[str, ...] = ()
        enable_profiles = False
        enable_per_page_selection = False
        per_page_choices: tuple[int, ...] = (10, 25, 50, 100)

    def __init__(
        self,
        *args: Any,
        template_kit: str | None = None,
        template_name: str | None = None,
        name: str = "",
        enable_column_selection: bool | None = None,
        enable_profiles: bool | None = None,
        enable_per_page_selection: bool | None = None,
        **kwargs: Any,
    ) -> None:
        # Extract filter-related kwargs
        self.filterset = kwargs.pop("filterset", None)
        self.table_name = name  # For Datastar signals like table_<name>
        explicit_kit = template_kit is not None
        super().__init__(*args, **kwargs)

        # Column selection: kwarg > Meta > default
        if enable_column_selection is not None:
            self.enable_column_selection = enable_column_selection
        else:
            self.enable_column_selection = getattr(
                self.Meta, "enable_column_selection", False
            )

        self.pinned_columns: tuple[str, ...] = getattr(
            self.Meta, "pinned_columns", ()
        )

        # Profiles: kwarg > Meta > default
        if enable_profiles is not None:
            self.enable_profiles = enable_profiles
        else:
            self.enable_profiles = getattr(self.Meta, "enable_profiles", False)

        # Per-page selection: kwarg > Meta > default
        if enable_per_page_selection is not None:
            self.enable_per_page_selection = enable_per_page_selection
        else:
            self.enable_per_page_selection = getattr(
                self.Meta, "enable_per_page_selection", False
            )

        self.per_page_choices: tuple[int, ...] = getattr(
            self.Meta, "per_page_choices", (10, 25, 50, 100)
        )

        # all_columns_meta is populated by RequestConfig.configure()
        self.all_columns_meta: list[dict[str, Any]] = []

        # Profile metadata - populated by RequestConfig.configure()
        self.profiles_list: list[dict[str, Any]] = []
        self.active_profile: dict[str, Any] | None = None
        self.current_per_page: int | None = None

        # Setup template based on template_kit
        # Priority: template_name kwarg > template_kit kwarg > Meta.template_kit > settings
        from django.conf import settings

        if template_name:
            # Explicit template_name takes highest priority
            self._meta.template_name = template_name
        elif (
            explicit_kit
            or not getattr(self._meta, "template_name", None)
            or self._meta.template_name == "django_tables2/table.html"
        ):
            if template_kit is None:
                default_kit = getattr(settings, "TABLE_DEFAULT_TEMPLATE_KIT", "bootstrap")
                template_kit = getattr(self.Meta, "template_kit", None) or default_kit
            self._meta.template_name = f"rg_table/{template_kit}/table.html"
