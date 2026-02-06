# Template Kits

rg.table provides pre-built templates for Bootstrap 5 and Bulma CSS frameworks.

## Choosing a Template Kit

Set the template kit in your table's Meta class:

```python
class BookTable(Table):
    # ... columns ...

    class Meta(TableMeta):
        template_kit = "bootstrap"  # Bootstrap 5
        # or
        template_kit = "bulma"      # Bulma CSS
```

## Global Default

Set a project-wide default in your Django settings:

```python
TABLE_DEFAULT_TEMPLATE_KIT = "bootstrap"
```

## Template Structure

Each kit provides these templates:

- `rg_table/{kit}/table.html` - Main table template
- `rg_table/{kit}/table_body.html` - Table body (rows)
- `rg_table/{kit}/paginator_simple.html` - Standard pagination
- `rg_table/{kit}/paginator_infinite.html` - Infinite scroll pagination
- `rg_table/{kit}/table_filtered.html` - Table with filter form
- `rg_table/{kit}/table_infinite.html` - Infinite scroll variant

## Overriding Templates

Create templates in your project's template directory:

```
templates/
└── rg_table/
    └── bootstrap/
        └── table.html  # Your custom template
```

Or specify a custom template directly:

```python
class Meta(TableMeta):
    template_name = "myapp/custom_table.html"
```
