# Examples

The repository includes a complete example Django project demonstrating all features.

## Running the Examples

```bash
cd examples
uv venv
source .venv/bin/activate

# Install rg.table in editable mode
uv pip install -e "..[all]"

# Run migrations
python manage.py migrate

# Import test data (GeoNames cities)
python manage.py import_geonames --dataset=cities15000

# Start the server
python manage.py runserver
```

Visit http://localhost:8000/geodata/ to see the demos.

## Available Demos

### Plain Table

Basic table with pagination, no sorting or filtering.

### Sortable Table

Table with clickable column headers for sorting.

### Filtered Table

Table with django-filter integration showing search and dropdown filters.

### Infinite Scroll

Datastar-powered infinite scrolling that loads more rows as you scroll.

### Column Selection

Sortable table with a "Columns" dropdown that lets users show/hide columns. Preferences persist in the session across page loads.

## Template Kits

Each demo is available in both Bootstrap 5 and Bulma versions to showcase the different styling options.
