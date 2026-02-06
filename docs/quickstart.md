# Quick Start

## Installation

Install rg.table with pip:

```bash
pip install rg-table
```

Or with optional dependencies:

```bash
pip install rg-table[filters]  # Include django-filter support
```

## Configuration

Add to your Django settings:

```python
INSTALLED_APPS = [
    # ...
    "django_tables2",
    "rg.table",
    # Optional: "django_filters",
]

# Optional: Set default template kit (default: "bootstrap")
TABLE_DEFAULT_TEMPLATE_KIT = "bootstrap"  # or "bulma"
```

## Create a Table

Define a table class:

```python
# tables.py
import django_tables2 as tables
from rg.table import Table, TableMeta

from .models import Book

class BookTable(Table):
    title = tables.Column()
    author = tables.Column()
    published = tables.DateColumn()
    price = tables.Column()

    class Meta(TableMeta):
        model = Book
        template_kit = "bootstrap"
        fields = ("title", "author", "published", "price")
```

## Use in a View

```python
# views.py
from django.shortcuts import render
from rg.table import RequestConfig

from .models import Book
from .tables import BookTable

def book_list(request):
    queryset = Book.objects.all()
    table = BookTable(queryset)
    RequestConfig(request, paginate={"per_page": 25}).configure(table)
    return render(request, "books/list.html", {"table": table})
```

## Render in Template

```html
{% load django_tables2 %}

<div class="container">
    <h1>Books</h1>
    {% render_table table %}
</div>
```

## Enable Sorting

```python
class BookTable(Table):
    title = tables.Column(orderable=True)
    author = tables.Column(orderable=True)
    published = tables.DateColumn(orderable=True)

    class Meta(TableMeta):
        model = Book
        template_kit = "bootstrap"
        orderable = True  # Enable sorting globally
```

## Enable Filtering

First, create a filterset:

```python
# filters.py
import django_filters

from .models import Book

class BookFilterSet(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr="icontains")
    author = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Book
        fields = ["title", "author"]
```

Then use in your table:

```python
class BookTable(Table):
    # ... columns ...

    class Meta(TableMeta):
        model = Book
        template_kit = "bootstrap"
        filterset_class = BookFilterSet
```

## Enable Infinite Scroll

```python
class BookTable(Table):
    # ... columns ...

    class Meta(TableMeta):
        model = Book
        template_kit = "bootstrap"
        infinite_scroll = True
```

This uses Datastar for seamless infinite scrolling without page reloads.
