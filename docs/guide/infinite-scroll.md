# Infinite Scroll

Load more data seamlessly as the user scrolls.

## Enable Infinite Scroll

```python
class BookTable(Table):
    # ... columns ...

    class Meta(TableMeta):
        template_kit = "bootstrap"
        infinite_scroll = True
```

## How It Works

Infinite scroll uses [Datastar](https://data-star.dev/) to:

1. Detect when the user scrolls near the bottom
2. Fetch the next page via AJAX
3. Append new rows without page reload

## Template

Use the infinite scroll template:

```python
table = BookTable(
    queryset,
    template_name="rg_table/bootstrap/table_infinite.html",
)
```

## View Setup

```python
from rg.table import table_render

def book_list(request):
    queryset = Book.objects.all()
    table = BookTable(queryset)
    RequestConfig(request, paginate={"per_page": 25}).configure(table)

    # table_render handles Datastar partial responses
    return table_render(request, "books/list.html", {"table": table})
```

The `table_render` helper automatically detects Datastar requests and returns only the table body for appending.
