"""URL configuration for geodata app."""

from django.urls import path

from . import views

app_name = "geodata"

urlpatterns = [
    # Index - table variation selector (per kit)
    path("bootstrap/", views.index_bootstrap, name="index-bootstrap"),
    path("bulma/", views.index_bulma, name="index-bulma"),

    # Bootstrap tables
    path("bootstrap/plain/", views.plain_table_bootstrap, name="plain-bootstrap"),
    path("bootstrap/sortable/", views.sortable_table_bootstrap, name="sortable-bootstrap"),
    path("bootstrap/filtered/", views.filtered_table_bootstrap, name="filtered-bootstrap"),
    path("bootstrap/infinite/", views.infinite_table_bootstrap, name="infinite-bootstrap"),

    # Bulma tables
    path("bulma/plain/", views.plain_table_bulma, name="plain-bulma"),
    path("bulma/sortable/", views.sortable_table_bulma, name="sortable-bulma"),
    path("bulma/filtered/", views.filtered_table_bulma, name="filtered-bulma"),
    path("bulma/infinite/", views.infinite_table_bulma, name="infinite-bulma"),

    # Default redirect to bootstrap
    path("", views.index_redirect, name="index"),
]
