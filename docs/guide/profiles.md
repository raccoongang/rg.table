# Profiles

rg.table supports **named profiles** — persistent, database-backed table configurations that authenticated users can save, load, and switch between. Each profile stores column visibility, per-page size, and sort order.

Anonymous users continue to use session-only preferences (column selection, per-page) as before.

## Architecture

Profiles follow an **explicit save** model:

1. Changes (column visibility, per-page) are applied to the **session** immediately.
2. The user explicitly **saves** those changes to a named profile in the database.
3. Loading a profile copies its data **from the database into the session**.

```
Session (working state)          DB (persistent state)
┌──────────────────────┐         ┌─────────────────────┐
│ columns: [col1, ...] │  save   │ TableProfile        │
│ per_page: 25         │ ──────> │  .columns (JSON)    │
│ active_profile: {id, │         │  .per_page (int)    │
│   name}              │ <────── │  .sort_order (JSON) │
└──────────────────────┘  load   │  .name, .is_default │
                                 └─────────────────────┘
```

## Enabling Profiles

Set `enable_profiles = True` in your table's Meta class. You'll typically also want `enable_column_selection` and `enable_per_page_selection`:

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
        enable_profiles = True
        enable_per_page_selection = True
        per_page_choices = (10, 25, 50, 100)
        pinned_columns = ("title",)
```

Or pass as constructor kwargs:

```python
table = BookTable(queryset, name="books", enable_profiles=True)
```

!!! important
    The table must have a `name` set (via the constructor kwarg) for profiles to work. The name is used as the session/database key.

## View Setup

No changes are needed in your view — `RequestConfig` handles everything:

```python
def book_list(request):
    queryset = Book.objects.all()
    table = BookTable(queryset, name="books")
    RequestConfig(request, paginate={"per_page": 25}).configure(table)
    return table_render(request, "books/list.html", {"table": table})
```

Make sure to run migrations so the `TableProfile` model is created:

```bash
python manage.py migrate rg_table
```

## Profile Actions

The profile selector dropdown appears in the table toolbar (alongside the column selector). It supports the following actions:

- **Load** — click a profile name to load it. Columns, per-page, and sort order are applied from the profile into the session.
- **Save** — update the currently active profile with the current session state.
- **Save as** — create a new profile from the current session state. Enter a name and click OK.
- **Set as default** — mark the active profile as the default. On first visit, the default profile is auto-loaded.
- **Delete** — remove the active profile from the database.

All actions use Datastar `@post` to submit a form with the `_profile_action` sentinel and optional `_profile_id` / `_profile_name` parameters.

## Default Profile

Each user can have one default profile per table. When an authenticated user visits a table for the first time (no active profile in the session), their default profile is automatically loaded.

To set a default profile, use the "Set as default" action in the profile dropdown, or programmatically:

```python
from rg.table.profiles import set_default_profile

set_default_profile(profile_id=5, user=request.user, table_name="books")
```

## Anonymous Users

Anonymous (unauthenticated) users:

- **Do not** see the profile selector dropdown (profiles_list is empty).
- **Can still** use column selection and per-page selection via the session.
- Profile actions in POST data are silently ignored.

## Per-Page Selection

Per-page selection works independently from profiles but integrates with them. Enable it with `enable_per_page_selection = True`:

```python
class Meta(TableMeta):
    enable_per_page_selection = True
    per_page_choices = (10, 25, 50, 100)  # default choices
```

A row of buttons appears below the paginator. Clicking a button stores the preference in the session and re-renders the table. The current per-page value is highlighted.

Per-page selection precedence (highest to lowest):

1. URL query parameter (`?per_page=50`)
2. Session preference (from per-page button or loaded profile)
3. `RequestConfig` paginate default

## TableProfile Model

The `TableProfile` model stores persistent profiles:

```python
from rg.table import TableProfile
```

| Field        | Type             | Description                          |
|--------------|------------------|--------------------------------------|
| `user`       | ForeignKey       | Link to AUTH_USER_MODEL              |
| `table_name` | CharField(255)   | Table name (matches `name` kwarg)    |
| `name`       | CharField(100)   | Profile display name                 |
| `is_default` | BooleanField     | Whether this is the user's default   |
| `columns`    | JSONField        | List of visible column names         |
| `per_page`   | PositiveInteger  | Items per page (nullable)            |
| `sort_order` | JSONField        | List of sort fields (e.g. `["-name"]`) |
| `created_at` | DateTimeField    | Auto-set on creation                 |
| `updated_at` | DateTimeField    | Auto-set on save                     |

A unique constraint ensures no two profiles share the same `(user, table_name, name)`.

## Programmatic API

Profile CRUD helpers are available in `rg.table.profiles`:

```python
from rg.table.profiles import (
    list_profiles,
    save_profile,
    save_as_profile,
    load_profile,
    delete_profile,
    set_default_profile,
    get_default_profile,
)

# List all profiles for a user/table
profiles = list_profiles(user, "books")

# Create a new profile from current session state
profile = save_as_profile(request.session, user, "books", "Compact View")

# Load a profile into the session
load_profile(request.session, profile)

# Update an existing profile from session state
save_profile(request.session, user, "books", profile.pk)

# Delete a profile
delete_profile(profile.pk, user)

# Set/get default
set_default_profile(profile.pk, user, "books")
default = get_default_profile(user, "books")
```

## Session Keys

Profiles use these session keys (per table_name):

| Key pattern                      | Value                      | Description                |
|----------------------------------|----------------------------|----------------------------|
| `rg_table:columns:{name}`        | `["col1", "col2"]`         | Visible columns (existing) |
| `rg_table:per_page:{name}`       | `25`                       | Per-page preference        |
| `rg_table:sort:{name}`           | `["-col1", "col2"]`        | Sort order (for future)    |
| `rg_table:active_profile:{name}` | `{"id": 5, "name": "..."}` | Active profile metadata    |

Session helpers for reading/writing these keys:

```python
from rg.table.config import (
    get_per_page_preference, set_per_page_preference,
    get_sort_preference, set_sort_preference,
    get_active_profile_info, set_active_profile_info,
    clear_active_profile_info,
)
```

## Stale Profiles

When loading a profile, columns that no longer exist in the table definition are silently ignored. The existing column selection logic already handles this — it filters stored column names against the current table's column set and enforces pinned columns.
