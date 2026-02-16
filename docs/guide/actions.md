# Row Selection & Actions

rg.table supports row selection with checkboxes and bulk actions (delete, export, custom handlers). The action bar with a "Select all" toggle, action dropdown, and "Go" button appears automatically when actions are defined.

## Defining Actions

Add actions to your table via the Meta class:

```python
from rg.table import Table, TableAction, TableMeta

def delete_selected(request, table, selected_pks):
    MyModel.objects.filter(pk__in=selected_pks).delete()
    return None  # redirect back (PRG)

class MyTable(Table):
    name = tables.Column()
    email = tables.Column()

    class Meta(TableMeta):
        template_kit = "bootstrap"
        actions = (
            TableAction(
                name="delete",
                label="Delete selected",
                handler=delete_selected,
                confirm="Are you sure you want to delete the selected rows?",
            ),
        )
```

Or pass actions as a constructor kwarg:

```python
table = MyTable(queryset, name="mytable", actions=(
    TableAction("delete", "Delete selected", delete_selected),
))
```

## TableAction

```python
@dataclass(frozen=True)
class TableAction:
    name: str              # Unique identifier (e.g. "delete", "export_csv")
    label: str             # Display text in the action dropdown
    handler: Callable      # (request, table, selected_pks: list[str]) -> HttpResponse | None
    requires_selection: bool = True   # Skip handler when nothing is selected
    confirm: str | None = None        # Browser confirm() message before executing
```

**Handler return values:**

- `None` — redirect back to the same page (Post/Redirect/Get pattern)
- `HttpResponse` — returned directly (e.g. file download)

## Row ID Field

By default, the primary key (`pk`) identifies each row. Override with `row_id_field`:

```python
class Meta(TableMeta):
    actions = (...)
    row_id_field = "geonameid"  # use a different field
```

Or as a constructor kwarg:

```python
table = MyTable(queryset, name="mytable", row_id_field="uuid")
```

## View Setup

Use `table_render` — it handles both regular page loads and Datastar SSE requests, and dispatches action form submissions:

```python
from rg.table import RequestConfig, table_render

def my_view(request):
    queryset = MyModel.objects.all()
    table = MyTable(queryset, name="mytable")
    RequestConfig(request, paginate={"per_page": 25}).configure(table)
    return table_render(request, "myapp/list.html", {"table": table})
```

!!! important
    The table must have a `name` set (via the constructor kwarg) for actions to work. The name is used for HTML element IDs and Datastar signals.

## How It Works

1. **Checkbox column** — when actions are defined, a checkbox column is prepended to each row automatically. Each checkbox has `name="_selected"` and `value="{row_id}"`.
2. **Select all** — the "Select all" checkbox in the action bar toggles all visible checkboxes via a Datastar signal.
3. **Action dropdown** — lists all defined actions by label.
4. **Go button** — submits the form. The server reads the selected action and checked row IDs from POST data.
5. **Handler dispatch** — `table_render` calls the matching action's handler with `(request, table, selected_pks)`.
6. **Page navigation** — when the user navigates to another page (next/prev), selections are cleared automatically.

## Confirmation Dialog

Actions with a `confirm` message show a browser `confirm()` dialog before submitting. If the user cancels, the form is not submitted.

```python
TableAction(
    "delete", "Delete selected", delete_handler,
    confirm="Are you sure you want to delete the selected rows?",
)
```

Actions with `confirm` are also blocked when "Select all" is checked, to prevent accidental bulk operations on all visible rows. The user must select specific rows instead.

## Export Actions

rg.table includes built-in CSV and XLSX export helpers:

```python
from rg.table import TableAction, make_csv_export, make_xlsx_export

class MyTable(Table):
    class Meta(TableMeta):
        actions = (
            TableAction("export_csv", "Export CSV", make_csv_export(), requires_selection=False),
            TableAction("export_xlsx", "Export XLSX", make_xlsx_export(), requires_selection=False),
        )
```

With `requires_selection=False`, these export all rows when nothing is selected, or only the selected rows otherwise.

XLSX export requires the `xlsxwriter` package.

### ExportMixin

For convenience, `ExportMixin` adds CSV (and XLSX if available) export actions automatically:

```python
from rg.table import Table, TableMeta
from rg.table.export import ExportMixin

class MyTable(ExportMixin, Table):
    name = tables.Column()

    class Meta(TableMeta):
        actions = (
            TableAction("delete", "Delete selected", delete_handler),
        )
    # Result: actions = (delete, export_csv, export_xlsx)
```

The mixin appends export actions after any actions defined in Meta or the constructor.

## Custom Export Filenames

```python
make_csv_export(filename="books.csv")
make_xlsx_export(filename="books.xlsx")
```

## Writing Custom Handlers

A handler receives `(request, table, selected_pks)` where `selected_pks` is a `list[str]` of row IDs from the checked checkboxes.

```python
def archive_selected(request, table, selected_pks):
    MyModel.objects.filter(pk__in=selected_pks).update(archived=True)
    return None  # PRG redirect

def export_json(request, table, selected_pks):
    import json
    qs = MyModel.objects.filter(pk__in=selected_pks)
    data = list(qs.values("id", "name", "email"))
    return HttpResponse(
        json.dumps(data, indent=2),
        content_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="export.json"'},
    )
```

## Combining with Other Features

Actions work alongside column selection, profiles, and per-page selection:

```python
class MyTable(ExportMixin, Table):
    class Meta(TableMeta):
        template_kit = "bootstrap"
        orderable = True
        enable_column_selection = True
        pinned_columns = ("name",)
        enable_profiles = True
        enable_per_page_selection = True
        actions = (
            TableAction("delete", "Delete selected", delete_handler,
                        confirm="Delete selected rows?"),
        )
```

## Template Placement

The action bar and checkboxes are included automatically in all table templates (`table.html`, `table_filtered.html`) for both Bootstrap and Bulma kits. They render only when `table.actions` is non-empty.
