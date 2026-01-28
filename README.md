# ok.table4

Django table rendering helper extending django-tables2 with Bootstrap/Bulma templates and Datastar integration.

## Installation



## Quick Start



## Features

- Bootstrap 5 and Bulma CSS templates
- Datastar integration for reactive tables
- Optional dynamic columns
- django-filter integration
- Sorting support

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/avkoval/rg.table4.git
cd rg.table4

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv pip install -e ".[all]"
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with coverage
uv run pytest --cov=src/rg/table4

# Run specific test file
uv run pytest tests/test_tables.py

# Run specific test class or method
uv run pytest tests/test_tables.py::TestTable4Creation
uv run pytest tests/test_tables.py::TestTable4Creation::test_table_creation_with_data
```

### Linting and Type Checking

```bash
# Run ruff linter
uv run ruff check src/ tests/

# Run ruff formatter
uv run ruff format src/ tests/

# Run mypy type checker
uv run mypy src/
```

## License

MIT
