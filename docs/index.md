# rg.table

**Django table rendering helper with Bootstrap/Bulma templates and Datastar integration.**

rg.table extends [django-tables2](https://django-tables2.readthedocs.io/) to provide:

- Pre-built templates for **Bootstrap 5** and **Bulma** CSS frameworks
- **Datastar** integration for reactive/dynamic tables
- **Infinite scroll** pagination
- Optional **django-filter** integration
- **User column selection** with session persistence
- **Named profiles** with database persistence for authenticated users
- **Per-page selection** with session persistence
- **Row selection & bulk actions** (delete, export CSV/XLSX, custom handlers)
- Clean, consistent API

## Installation

```bash
pip install rg-table
```

Or with uv:

```bash
uv add rg-table
```

## Quick Example

```python
import django_tables2 as tables
from rg.table import Table, TableMeta

class BookTable(Table):
    title = tables.Column()
    author = tables.Column()
    published = tables.DateColumn()

    class Meta(TableMeta):
        template_kit = "bootstrap"  # or "bulma"
```

```python
# views.py
from rg.table import RequestConfig

def book_list(request):
    table = BookTable(Book.objects.all())
    RequestConfig(request, paginate={"per_page": 25}).configure(table)
    return render(request, "books/list.html", {"table": table})
```

```html
<!-- template -->
{% load django_tables2 %}
{% render_table table %}
```

## Features

### Template Kits

Choose between Bootstrap 5 and Bulma templates:

```python
class Meta(TableMeta):
    template_kit = "bootstrap"  # Bootstrap 5 styling
    # or
    template_kit = "bulma"      # Bulma CSS styling
```

### Infinite Scroll

Enable Datastar-powered infinite scrolling:

```python
class Meta(TableMeta):
    template_kit = "bootstrap"
    infinite_scroll = True
```

### Filtering

Integrate with django-filter:

```python
class Meta(TableMeta):
    template_kit = "bootstrap"
    filterset_class = BookFilterSet
```

### Column Selection

Let users choose which columns to display:

```python
class Meta(TableMeta):
    template_kit = "bootstrap"
    enable_column_selection = True
    pinned_columns = ("title",)  # always visible
```

### Profiles

Save and load named table configurations (columns, per-page, sort):

```python
class Meta(TableMeta):
    template_kit = "bootstrap"
    enable_column_selection = True
    enable_profiles = True
    enable_per_page_selection = True
```

### Row Selection & Actions

Add bulk actions with row checkboxes:

```python
from rg.table import TableAction
from rg.table.export import ExportMixin

class Meta(TableMeta):
    template_kit = "bootstrap"
    actions = (
        TableAction("delete", "Delete selected", delete_handler,
                    confirm="Delete selected rows?"),
    )

# Or use ExportMixin for CSV/XLSX export:
class MyTable(ExportMixin, Table):
    ...
```

### Per-Page Selection

Let users choose how many rows to display:

```python
class Meta(TableMeta):
    template_kit = "bootstrap"
    enable_per_page_selection = True
    per_page_choices = (10, 25, 50, 100)
```

## Requirements

- Python 3.12+
- Django 5.0+
- django-tables2 2.7+

## License

MIT License
