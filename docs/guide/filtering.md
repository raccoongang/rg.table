# Filtering

Integrate django-filter for powerful data filtering.

## Setup

Install django-filter:

```bash
pip install django-filter
```

Add to INSTALLED_APPS:

```python
INSTALLED_APPS = [
    # ...
    "django_filters",
]
```

## Create a FilterSet

```python
# filters.py
import django_filters
from .models import Book

class BookFilterSet(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr="icontains")
    author = django_filters.CharFilter(lookup_expr="icontains")
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")

    class Meta:
        model = Book
        fields = ["title", "author"]
```

## Connect to Table

```python
class BookTable(Table):
    # ... columns ...

    class Meta(TableMeta):
        template_kit = "bootstrap"
        filterset_class = BookFilterSet
```

## View Setup

```python
def book_list(request):
    queryset = Book.objects.all()
    filterset = BookFilterSet(request.GET, queryset=queryset)

    table = BookTable(filterset.qs)
    table.filterset = filterset

    RequestConfig(request, paginate={"per_page": 25}).configure(table)
    return render(request, "books/list.html", {"table": table})
```

## Filtered Template

Use the filtered template for the filter form:

```python
table = BookTable(
    filterset.qs,
    template_name="rg_table/bootstrap/table_filtered.html",
)
```
