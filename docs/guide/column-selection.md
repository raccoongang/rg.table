# Column Selection

rg.table allows end users to choose which columns are visible in a table. Preferences are stored in the Django session and persist across page loads.

## Enabling Column Selection

Set `enable_column_selection = True` in your table's Meta class:

```python
class BookTable(Table):
    title = tables.Column()
    author = tables.Column()
    published = tables.DateColumn()
    isbn = tables.Column()
    price = tables.Column()

    class Meta(TableMeta):
        template_kit = "bootstrap"
        enable_column_selection = True
```

Or pass it as a constructor kwarg:

```python
table = BookTable(queryset, name="books", enable_column_selection=True)
```

!!! important
    The table must have a `name` set (via the constructor kwarg) for column selection to work. The name is used as the session storage key.

## View Setup

Use `RequestConfig` as usual — column selection is handled automatically:

```python
def book_list(request):
    queryset = Book.objects.all()
    table = BookTable(queryset, name="books")
    RequestConfig(request, paginate={"per_page": 25}).configure(table)
    return table_render(request, "books/list.html", {"table": table})
```

The column selector UI appears automatically above the table. Users toggle checkboxes and click **Apply** to update the visible columns.

## Pinned Columns

Some columns should always be visible (e.g. a name or identifier). Mark them as pinned:

```python
class BookTable(Table):
    title = tables.Column()
    author = tables.Column()
    published = tables.DateColumn()
    isbn = tables.Column()
    price = tables.Column()

    class Meta(TableMeta):
        enable_column_selection = True
        pinned_columns = ("title",)  # Cannot be hidden by the user
```

Pinned columns appear as disabled (checked but not clickable) in the column selector dropdown. They are enforced server-side — even if the form data omits a pinned column, the server adds it back.

## How It Works

1. **First visit** — all columns are visible (no preference stored yet).
2. **User clicks "Columns"** — a dropdown opens with a checkbox for each column.
3. **User toggles checkboxes and clicks "Apply"** — a Datastar `@post` sends the form to the same URL, preserving current page/sort/filter params.
4. **Server processes the request** — `RequestConfig.configure()` reads the selected columns from `request.POST`, validates them, enforces pinned columns and minimum visibility (at least one column), and saves the preference to the session.
5. **Subsequent page loads** — the stored preference is read from the session and applied automatically.

## Session Storage

Preferences are stored in the Django session under the key `rg_table:columns:{table_name}`.

You can read or write preferences programmatically:

```python
from rg.table.config import get_column_preference, set_column_preference

# Read (returns list[str] or None)
columns = get_column_preference(request.session, "books")

# Write
set_column_preference(request.session, "books", ["title", "author", "price"])
```

This is useful for pre-populating preferences or building a "reset to defaults" action.

## Template Placement

The column selector is included automatically in all table templates:

- `table.html` — above the table body (via `{% block columns_selector %}`)
- `table_filtered.html` — in the filter bar, right-aligned
- `table_infinite.html` — inherited from `table.html`

It only renders when `enable_column_selection` is truthy and `all_columns_meta` is populated (i.e. after `RequestConfig.configure()` runs).

## Future: Database Profiles

The session-based approach is designed to extend to database-backed profiles. The planned approach:

1. Create a model storing `(user, table_name, columns, is_default)`.
2. On login, load the user's default profile into the session.
3. The session helpers (`get_column_preference` / `set_column_preference`) remain the interface — no changes needed to `RequestConfig` or templates.
