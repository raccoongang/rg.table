# Settings Reference

## Django Settings

### TABLE_DEFAULT_TEMPLATE_KIT

Default template kit for all tables.

```python
TABLE_DEFAULT_TEMPLATE_KIT = "bootstrap"  # or "bulma"
```

**Default:** `"bootstrap"`

## INSTALLED_APPS

Required apps for rg.table:

```python
INSTALLED_APPS = [
    # ...
    "django_tables2",      # Required
    "rg.table",            # Required
    "django_filters",      # Optional: for filtering
]
```

## Template Configuration

Ensure APP_DIRS is enabled for template discovery:

```python
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,  # Required
        # ...
    },
]
```
