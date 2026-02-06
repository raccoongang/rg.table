# Pagination

Control how large datasets are paginated.

## Basic Pagination

```python
from rg.table import RequestConfig

def book_list(request):
    table = BookTable(Book.objects.all())
    RequestConfig(request, paginate={"per_page": 25}).configure(table)
    return render(request, "books/list.html", {"table": table})
```

## Configuration Options

```python
RequestConfig(request, paginate={
    "per_page": 25,        # Items per page
    "page": 1,             # Starting page
    "orphans": 3,          # Minimum items on last page
}).configure(table)
```

## Disable Pagination

```python
RequestConfig(request, paginate=False).configure(table)
```

## URL Parameters

Pagination uses URL query parameters:

- `?page=2` - Go to page 2
- `?per_page=50` - Show 50 items per page
