# rg.table

**Django table rendering helper with Bootstrap/Bulma templates and Datastar integration.**

rg.table extends [django-tables2](https://django-tables2.readthedocs.io/) to provide:

- Pre-built templates for **Bootstrap 5** and **Bulma** CSS frameworks
- **Datastar** integration for reactive/dynamic tables
- **Infinite scroll** pagination
- Optional **django-filter** integration
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

## Requirements

- Python 3.12+
- Django 5.0+
- django-tables2 2.7+

## License

MIT License
