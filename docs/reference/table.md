# Table Class Reference

## Table

The main table class extending `django_tables2.Table`.

```python
from rg.table import Table, TableMeta

class MyTable(Table):
    name = tables.Column()

    class Meta(TableMeta):
        template_kit = "bootstrap"
```

### Constructor

```python
Table(data, template_kit=None, name=None, enable_column_selection=None, **kwargs)
```

**Parameters:**

- `data` - QuerySet, list, or other iterable
- `template_kit` - Override Meta.template_kit ("bootstrap" or "bulma")
- `name` - Table name for HTML id attributes and session key
- `enable_column_selection` - Override Meta.enable_column_selection
- `**kwargs` - Passed to django_tables2.Table

### Meta Options

Inherit from `TableMeta` for rg.table features:

| Option                    | Type  | Default     | Description                               |
|---------------------------|-------|-------------|-------------------------------------------|
| `template_kit`            | str   | "bootstrap" | CSS framework ("bootstrap" or "bulma")    |
| `infinite_scroll`         | bool  | False       | Enable infinite scroll pagination         |
| `filterset_class`         | class | None        | django-filter FilterSet class             |
| `orderable`               | bool  | False       | Enable column sorting                     |
| `enable_column_selection` | bool  | False       | Enable user column selection              |
| `pinned_columns`          | tuple | ()          | Columns that cannot be hidden by the user |
| `model`                   | class | None        | Django model for automatic columns        |
| `fields`                  | tuple | None        | Fields to include                         |
| `exclude`                 | tuple | None        | Fields to exclude                         |
| `template_name`           | str   | None        | Override default template                 |

## RequestConfig

Configure table from request.

```python
from rg.table import RequestConfig

RequestConfig(request, paginate={"per_page": 25}).configure(table)
```

### Parameters

- `request` - Django HttpRequest
- `paginate` - Pagination config dict or False to disable

### Pagination Options

```python
paginate={
    "per_page": 25,
    "page": 1,
    "orphans": 0,
}
```

## table_render

Render helper with Datastar support.

```python
from rg.table import table_render

return table_render(request, template_name, context)
```

Returns partial HTML for Datastar requests, full page otherwise.
