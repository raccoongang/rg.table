# rg.table

[![CI](https://github.com/raccoongang/rg.table/actions/workflows/ci.yml/badge.svg)](https://github.com/raccoongang/rg.table/actions/workflows/ci.yml)
[![Documentation](https://github.com/raccoongang/rg.table/actions/workflows/docs.yml/badge.svg)](https://raccoongang.github.io/rg.table)

Django table rendering helper extending django-tables2 with Bootstrap/Bulma templates and Datastar integration.

## Installation

```bash
pip install rg-table
```

Or with uv:

```bash
uv add rg-table
```

## Quick Start

```python
# tables.py
import django_tables2 as tables
from rg.table import Table, TableMeta

class BookTable(Table):
    title = tables.Column()
    author = tables.Column()

    class Meta(TableMeta):
        template_kit = "bootstrap"  # or "bulma"
```

```python
# views.py
from rg.table import RequestConfig

def book_list(request):
    table = BookTable(Book.objects.all())
    RequestConfig(request, paginate={"per_page": 25}).configure(table)
    return render(request, "books/list.html", {"table": table})
```

```html
{% load django_tables2 %}
{% render_table table %}
```

## Features

- **Bootstrap 5 and Bulma CSS templates** - Pre-built, responsive table templates
- **Datastar integration** - Reactive tables with infinite scroll
- **django-filter integration** - Easy filtering with django-filter
- **Sorting support** - Clickable column headers for sorting

## Documentation

Full documentation: [https://raccoongang.github.io/rg.table](https://raccoongang.github.io/rg.table)

## Development

### Setup

```bash
git clone https://github.com/raccoongang/rg.table.git
cd rg.table

uv venv
source .venv/bin/activate
uv sync --all-extras
```

### Running Tests

```bash
.venv/bin/pytest
.venv/bin/pytest --cov=src/rg/table
```

### Running Examples

```bash
cd examples
uv venv
source .venv/bin/activate
uv pip install -e "..[all]"
python manage.py migrate
python manage.py import_geonames --dataset=cities15000
python manage.py runserver
```

Visit http://localhost:8000/geodata/

### Linting and Type Checking

```bash
.venv/bin/ruff check src/ tests/
.venv/bin/ruff format src/ tests/
.venv/bin/mypy src/
```

### Building Documentation

```bash
uv pip install mkdocs-material pymdown-extensions
mkdocs serve
```

## License

MIT
