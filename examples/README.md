# rg.table example project

Example Django project demonstrating rg.table - Django table rendering helper with Bootstrap/Bulma templates and Datastar integration.

## Setup

```bash
cd examples
uv venv
source .venv/bin/activate

# Install rg.table in editable mode from the parent directory
uv pip install -e "..[all]"

python manage.py migrate
```

## Importing Test Data

The project includes a `geodata` app with GeoNames geographical data for testing tables with large datasets.

### Import Commands

**Import cities with population > 15,000 (recommended for quick testing):**
```bash
python manage.py import_geonames --dataset=cities15000
```

**Import cities with population > 500 (larger dataset):**
```bash
python manage.py import_geonames --dataset=cities500
```

## Running the Development Server

```bash
python manage.py runserver
```

Then visit http://localhost:8000/geodata/ to see the examples.

## Examples

The geodata app demonstrates:

1. **Plain Table** - Basic table rendering with pagination
2. **Sortable Table** - Table with column sorting
3. **Filtered Table** - Table with django-filter integration
4. **Infinite Scroll** - Table with Datastar-powered infinite scrolling

Both Bootstrap and Bulma template kits are available.

## Project Structure

```
examples/               # This directory (inside rg.table repo)
├── manage.py
├── testsite/
│   ├── settings.py    # Adds ../../src to sys.path for local rg.table
│   └── urls.py
└── geodata/
    ├── models.py       # GeoName model
    ├── tables.py       # Table definitions
    ├── views.py        # Views demonstrating different table types
    ├── filters.py      # django-filter filtersets
    └── templates/
```

## Data Source

GeoNames data is downloaded from [GeoNames](https://download.geonames.org/export/dump/) and is licensed under [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/).
