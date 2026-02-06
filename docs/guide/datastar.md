# Datastar Integration

rg.table uses [Datastar](https://data-star.dev/) for reactive features.

## What is Datastar?

Datastar is a lightweight JavaScript library for building reactive web interfaces. It handles:

- AJAX requests
- DOM updates
- Event handling
- State management

## Features Using Datastar

### Infinite Scroll

Datastar detects scroll position and loads more data automatically.

### Sorting (AJAX)

Column headers can trigger AJAX requests to re-sort without page reload.

### Filtering (AJAX)

Filter form submissions can update the table via AJAX.

## Including Datastar

Add Datastar to your base template:

```html
<script src="https://cdn.jsdelivr.net/npm/@starfederation/datastar"></script>
```

Or install via npm:

```bash
npm install @starfederation/datastar
```

## The table_render Helper

Use `table_render` instead of Django's `render` for Datastar support:

```python
from rg.table import table_render

def book_list(request):
    table = BookTable(Book.objects.all())
    RequestConfig(request, paginate={"per_page": 25}).configure(table)
    return table_render(request, "books/list.html", {"table": table})
```

This helper:

1. Detects Datastar requests via the `Datastar-Request` header
2. Returns partial HTML (just the table body) for Datastar requests
3. Returns full page HTML for regular requests
