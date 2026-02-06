# Sorting

Enable column sorting for interactive data exploration.

## Enable Sorting

### Per-Column

```python
class BookTable(Table):
    title = tables.Column(orderable=True)
    author = tables.Column(orderable=True)
    published = tables.DateColumn(orderable=False)  # Not sortable
```

### Global

```python
class Meta(TableMeta):
    orderable = True  # All columns sortable by default
```

## How It Works

When sorting is enabled, column headers become clickable. Clicking toggles between ascending and descending order.

The sort state is preserved in the URL via query parameters (e.g., `?sort=title` or `?sort=-title`).

## Custom Sort Fields

```python
title = tables.Column(
    orderable=True,
    order_by=("title", "subtitle"),  # Sort by multiple fields
)
```
