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
Table(
    data,
    template_kit=None,
    name=None,
    enable_column_selection=None,
    enable_profiles=None,
    enable_per_page_selection=None,
    actions=None,
    row_id_field=None,
    **kwargs,
)
```

**Parameters:**

- `data` - QuerySet, list, or other iterable
- `template_kit` - Override Meta.template_kit ("bootstrap" or "bulma")
- `name` - Table name for HTML id attributes and session key
- `enable_column_selection` - Override Meta.enable_column_selection
- `enable_profiles` - Override Meta.enable_profiles
- `enable_per_page_selection` - Override Meta.enable_per_page_selection
- `actions` - Tuple of `TableAction` instances (overrides Meta.actions)
- `row_id_field` - Field name for row IDs in checkboxes (overrides Meta.row_id_field, default: "pk")
- `**kwargs` - Passed to django_tables2.Table

### Meta Options

Inherit from `TableMeta` for rg.table features:

| Option                      | Type  | Default          | Description                               |
|-----------------------------|-------|------------------|-------------------------------------------|
| `template_kit`              | str   | "bootstrap"      | CSS framework ("bootstrap" or "bulma")    |
| `infinite_scroll`           | bool  | False            | Enable infinite scroll pagination         |
| `filterset_class`           | class | None             | django-filter FilterSet class             |
| `orderable`                 | bool  | False            | Enable column sorting                     |
| `enable_column_selection`   | bool  | False            | Enable user column selection              |
| `pinned_columns`            | tuple | ()               | Columns that cannot be hidden by the user |
| `enable_profiles`           | bool  | False            | Enable named profile save/load            |
| `enable_per_page_selection` | bool  | False            | Enable per-page size selector             |
| `per_page_choices`          | tuple | (10, 25, 50, 100) | Allowed per-page sizes                  |
| `model`                     | class | None             | Django model for automatic columns        |
| `fields`                    | tuple | None             | Fields to include                         |
| `exclude`                   | tuple | None             | Fields to exclude                         |
| `template_name`             | str   | None             | Override default template                 |
| `actions`                   | tuple | ()               | Tuple of `TableAction` instances          |
| `row_id_field`              | str   | "pk"             | Field name for row IDs in checkboxes      |

### Instance Attributes (set by RequestConfig)

| Attribute         | Type           | Description                                      |
|-------------------|----------------|--------------------------------------------------|
| `all_columns_meta`| list[dict]     | Column metadata for column selector UI           |
| `profiles_list`   | list[dict]     | Available profiles (`{id, name, is_default}`)    |
| `active_profile`  | dict or None   | Active profile (`{id, name}`) or None            |
| `current_per_page`| int or None    | Current per-page value for template highlight    |

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
