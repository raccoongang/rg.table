# Template Tags Reference

rg.table uses django-tables2's template tags.

## render_table

Render a table in a template.

```html
{% load django_tables2 %}

{% render_table table %}
```

### With Custom Template

```html
{% render_table table "myapp/custom_table.html" %}
```

### Available Context

Inside the table template, you have access to:

- `table` - The table instance
- `table.columns` - Column definitions
- `table.rows` - Data rows
- `table.page` - Current page (if paginated)
- `table.paginator` - Paginator instance

## Table Attributes

Access table properties in templates:

```html
<!-- Table name -->
{{ table.table_name }}

<!-- Template kit -->
{{ table.template_kit }}

<!-- Check if paginated -->
{% if table.page %}
    Page {{ table.page.number }} of {{ table.paginator.num_pages }}
{% endif %}
```

## Filter Fields

When using filtering, access filter fields:

```html
{% if table.filterset %}
    <form method="get">
        {% for name, field in table.filter_fields %}
            {{ field.label }}: {{ field }}
        {% endfor %}
        <button type="submit">Filter</button>
    </form>
{% endif %}
```
