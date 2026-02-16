"""Tests for profiles feature (model, CRUD, session integration, RequestConfig)."""

from __future__ import annotations

import django_tables2 as tables
import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.template.loader import render_to_string
from django.test import RequestFactory

from rg.table import RequestConfig, Table, TableMeta, TableProfile
from rg.table.config import (
    PER_PAGE_SUBMIT_PARAM,
    PER_PAGE_VALUE_PARAM,
    PROFILE_ACTION_PARAM,
    PROFILE_ID_PARAM,
    PROFILE_NAME_PARAM,
    get_active_profile_info,
    get_column_preference,
    get_per_page_preference,
    get_sort_preference,
    set_column_preference,
    set_per_page_preference,
    set_sort_preference,
)
from rg.table.profiles import (
    delete_profile,
    get_default_profile,
    list_profiles,
    load_profile,
    save_as_profile,
    save_profile,
    set_default_profile,
)

# --- Test table classes ---


class ProfileTable(Table):
    """Table with profiles and column selection enabled."""

    id = tables.Column()
    name = tables.Column()
    country = tables.Column()
    population = tables.Column()

    class Meta(TableMeta):
        template_kit = "bootstrap"
        enable_column_selection = True
        enable_profiles = True
        enable_per_page_selection = True
        per_page_choices = (10, 25, 50, 100)


class PerPageTable(Table):
    """Table with per-page selection only."""

    id = tables.Column()
    name = tables.Column()

    class Meta(TableMeta):
        template_kit = "bootstrap"
        enable_per_page_selection = True
        per_page_choices = (10, 25, 50)


class NoProfileTable(Table):
    """Table without profiles (default)."""

    id = tables.Column()
    name = tables.Column()

    class Meta(TableMeta):
        template_kit = "bootstrap"


# --- Fixtures ---


@pytest.fixture
def data():
    return [
        {"id": i, "name": f"Item {i}", "country": "US", "population": i * 100}
        for i in range(1, 51)
    ]


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="testpass")


@pytest.fixture
def user2(db):
    return User.objects.create_user(username="testuser2", password="testpass2")


def _make_request(rf, user=None, get_params=None, post_params=None):
    """Create a request with a session dict and optional user."""
    if post_params:
        request = rf.post("/", post_params)
    else:
        request = rf.get("/", get_params or {})
    request.session = {}
    if user:
        request.user = user
    else:
        request.user = AnonymousUser()
    return request


# --- Session helper tests ---


class TestPerPageSessionHelpers:
    def test_get_returns_none_when_unset(self):
        session: dict = {}
        assert get_per_page_preference(session, "mytable") is None

    def test_set_and_get(self):
        session: dict = {}
        set_per_page_preference(session, "mytable", 25)
        assert get_per_page_preference(session, "mytable") == 25

    def test_separate_tables(self):
        session: dict = {}
        set_per_page_preference(session, "a", 10)
        set_per_page_preference(session, "b", 50)
        assert get_per_page_preference(session, "a") == 10
        assert get_per_page_preference(session, "b") == 50


class TestSortSessionHelpers:
    def test_get_returns_none_when_unset(self):
        session: dict = {}
        assert get_sort_preference(session, "mytable") is None

    def test_set_and_get(self):
        session: dict = {}
        set_sort_preference(session, "mytable", ["-name", "id"])
        assert get_sort_preference(session, "mytable") == ["-name", "id"]


class TestActiveProfileSessionHelpers:
    def test_get_returns_none_when_unset(self):
        session: dict = {}
        assert get_active_profile_info(session, "mytable") is None

    def test_set_and_get(self):
        from rg.table.config import set_active_profile_info

        session: dict = {}
        set_active_profile_info(session, "mytable", 5, "My View")
        info = get_active_profile_info(session, "mytable")
        assert info == {"id": 5, "name": "My View"}

    def test_clear(self):
        from rg.table.config import clear_active_profile_info, set_active_profile_info

        session: dict = {}
        set_active_profile_info(session, "mytable", 5, "My View")
        clear_active_profile_info(session, "mytable")
        assert get_active_profile_info(session, "mytable") is None


# --- Model tests ---


@pytest.mark.django_db
class TestTableProfileModel:
    def test_create(self, user):
        profile = TableProfile.objects.create(
            user=user,
            table_name="test",
            name="My View",
            columns=["id", "name"],
            per_page=25,
        )
        assert profile.pk is not None
        assert str(profile) == "My View (test)"

    def test_unique_constraint(self, user):
        TableProfile.objects.create(user=user, table_name="test", name="View A")
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            TableProfile.objects.create(user=user, table_name="test", name="View A")

    def test_different_users_same_name(self, user, user2):
        TableProfile.objects.create(user=user, table_name="test", name="View A")
        TableProfile.objects.create(user=user2, table_name="test", name="View A")
        assert TableProfile.objects.count() == 2

    def test_ordering(self, user):
        TableProfile.objects.create(user=user, table_name="test", name="Zebra")
        TableProfile.objects.create(user=user, table_name="test", name="Alpha")
        profiles = list(TableProfile.objects.filter(user=user))
        assert profiles[0].name == "Alpha"
        assert profiles[1].name == "Zebra"

    def test_default_values(self, user):
        profile = TableProfile.objects.create(
            user=user, table_name="test", name="Default"
        )
        assert profile.columns == []
        assert profile.per_page is None
        assert profile.sort_order == []
        assert profile.is_default is False


# --- Profile CRUD tests ---


@pytest.mark.django_db
class TestListProfiles:
    def test_list_empty(self, user):
        assert list(list_profiles(user, "test")) == []

    def test_list_returns_own_profiles(self, user, user2):
        TableProfile.objects.create(user=user, table_name="test", name="A")
        TableProfile.objects.create(user=user, table_name="test", name="B")
        TableProfile.objects.create(user=user2, table_name="test", name="C")
        result = list(list_profiles(user, "test"))
        assert len(result) == 2
        assert {p.name for p in result} == {"A", "B"}

    def test_list_filters_by_table_name(self, user):
        TableProfile.objects.create(user=user, table_name="test1", name="A")
        TableProfile.objects.create(user=user, table_name="test2", name="B")
        result = list(list_profiles(user, "test1"))
        assert len(result) == 1
        assert result[0].name == "A"


@pytest.mark.django_db
class TestSaveProfile:
    def test_save_updates_existing(self, user):
        profile = TableProfile.objects.create(
            user=user,
            table_name="test",
            name="My View",
            columns=["id"],
            per_page=10,
        )
        session: dict = {}
        set_column_preference(session, "test", ["id", "name", "country"])
        set_per_page_preference(session, "test", 50)

        result = save_profile(session, user, "test", profile.pk)
        assert result is not None
        profile.refresh_from_db()
        assert profile.columns == ["id", "name", "country"]
        assert profile.per_page == 50

    def test_save_sets_active_profile(self, user):
        profile = TableProfile.objects.create(
            user=user, table_name="test", name="My View"
        )
        session: dict = {}
        result = save_profile(session, user, "test", profile.pk)
        assert result is not None
        active = get_active_profile_info(session, "test")
        assert active is not None
        assert active["id"] == profile.pk

    def test_save_nonexistent_returns_none(self, user):
        session: dict = {}
        result = save_profile(session, user, "test", 99999)
        assert result is None

    def test_save_other_users_profile_returns_none(self, user, user2):
        profile = TableProfile.objects.create(
            user=user2, table_name="test", name="Not mine"
        )
        session: dict = {}
        result = save_profile(session, user, "test", profile.pk)
        assert result is None


@pytest.mark.django_db
class TestSaveAsProfile:
    def test_creates_new_profile(self, user):
        session: dict = {}
        set_column_preference(session, "test", ["id", "name"])
        set_per_page_preference(session, "test", 25)

        profile = save_as_profile(session, user, "test", "New View")
        assert profile.pk is not None
        assert profile.name == "New View"
        assert profile.columns == ["id", "name"]
        assert profile.per_page == 25

    def test_sets_active_profile(self, user):
        session: dict = {}
        profile = save_as_profile(session, user, "test", "New View")
        active = get_active_profile_info(session, "test")
        assert active is not None
        assert active["id"] == profile.pk
        assert active["name"] == "New View"


@pytest.mark.django_db
class TestLoadProfile:
    def test_populates_session(self, user):
        profile = TableProfile.objects.create(
            user=user,
            table_name="test",
            name="My View",
            columns=["id", "country"],
            per_page=50,
            sort_order=["-name"],
        )
        session: dict = {}
        load_profile(session, profile)

        assert get_column_preference(session, "test") == ["id", "country"]
        assert get_per_page_preference(session, "test") == 50
        assert get_sort_preference(session, "test") == ["-name"]
        assert get_active_profile_info(session, "test") == {
            "id": profile.pk,
            "name": "My View",
        }

    def test_empty_columns_not_overwritten(self, user):
        """Profile with empty columns doesn't overwrite existing session columns."""
        profile = TableProfile.objects.create(
            user=user, table_name="test", name="Minimal"
        )
        session: dict = {}
        set_column_preference(session, "test", ["id", "name"])
        load_profile(session, profile)
        # Empty columns in profile → session keeps old value
        assert get_column_preference(session, "test") == ["id", "name"]


@pytest.mark.django_db
class TestDeleteProfile:
    def test_delete_existing(self, user):
        profile = TableProfile.objects.create(
            user=user, table_name="test", name="My View"
        )
        assert delete_profile(profile.pk, user) is True
        assert TableProfile.objects.filter(pk=profile.pk).count() == 0

    def test_delete_nonexistent(self, user):
        assert delete_profile(99999, user) is False

    def test_delete_other_users_profile(self, user, user2):
        profile = TableProfile.objects.create(
            user=user2, table_name="test", name="Not mine"
        )
        assert delete_profile(profile.pk, user) is False
        assert TableProfile.objects.filter(pk=profile.pk).exists()


@pytest.mark.django_db
class TestSetDefaultProfile:
    def test_set_default(self, user):
        p1 = TableProfile.objects.create(
            user=user, table_name="test", name="A", is_default=True
        )
        p2 = TableProfile.objects.create(
            user=user, table_name="test", name="B"
        )
        set_default_profile(p2.pk, user, "test")

        p1.refresh_from_db()
        p2.refresh_from_db()
        assert p1.is_default is False
        assert p2.is_default is True

    def test_get_default_profile(self, user):
        TableProfile.objects.create(user=user, table_name="test", name="A")
        p2 = TableProfile.objects.create(
            user=user, table_name="test", name="B", is_default=True
        )
        default = get_default_profile(user, "test")
        assert default is not None
        assert default.pk == p2.pk

    def test_get_default_profile_none(self, user):
        TableProfile.objects.create(user=user, table_name="test", name="A")
        assert get_default_profile(user, "test") is None


# --- Table class tests ---


class TestTableMetaOptions:
    def test_profiles_disabled_by_default(self, data):
        table = NoProfileTable(data)
        assert table.enable_profiles is False

    def test_profiles_enabled_via_meta(self, data):
        table = ProfileTable(data, name="test")
        assert table.enable_profiles is True

    def test_profiles_enabled_via_kwarg(self, data):
        table = NoProfileTable(data, name="test", enable_profiles=True)
        assert table.enable_profiles is True

    def test_kwarg_overrides_meta(self, data):
        table = ProfileTable(data, name="test", enable_profiles=False)
        assert table.enable_profiles is False

    def test_per_page_selection_disabled_by_default(self, data):
        table = NoProfileTable(data)
        assert table.enable_per_page_selection is False

    def test_per_page_selection_enabled_via_meta(self, data):
        table = PerPageTable(data, name="test")
        assert table.enable_per_page_selection is True

    def test_per_page_choices_default(self, data):
        table = NoProfileTable(data)
        assert table.per_page_choices == (10, 25, 50, 100)

    def test_per_page_choices_from_meta(self, data):
        table = PerPageTable(data, name="test")
        assert table.per_page_choices == (10, 25, 50)

    def test_initial_profile_attrs(self, data):
        table = ProfileTable(data, name="test")
        assert table.profiles_list == []
        assert table.active_profile is None
        assert table.current_per_page is None


# --- RequestConfig profile integration tests ---


@pytest.mark.django_db
class TestRequestConfigProfiles:
    def test_save_as_via_post(self, rf, data, user):
        """POST with _profile_action=save_as creates a new profile."""
        request = _make_request(
            rf,
            user=user,
            post_params={
                PROFILE_ACTION_PARAM: "save_as",
                PROFILE_NAME_PARAM: "My View",
            },
        )
        set_column_preference(request.session, "test", ["id", "name"])

        table = ProfileTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)

        assert TableProfile.objects.filter(user=user, name="My View").exists()
        assert table.active_profile is not None
        assert table.active_profile["name"] == "My View"

    def test_load_via_post(self, rf, data, user):
        """POST with _profile_action=load loads profile into session."""
        profile = TableProfile.objects.create(
            user=user,
            table_name="test",
            name="Saved",
            columns=["id", "country"],
            per_page=50,
        )
        request = _make_request(
            rf,
            user=user,
            post_params={
                PROFILE_ACTION_PARAM: "load",
                PROFILE_ID_PARAM: str(profile.pk),
            },
        )
        table = ProfileTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)

        # Columns should reflect loaded profile
        visible = [col.name for col in table.columns]
        assert visible == ["id", "country"]
        assert table.active_profile is not None
        assert table.active_profile["name"] == "Saved"

    def test_save_via_post(self, rf, data, user):
        """POST with _profile_action=save updates the active profile."""
        profile = TableProfile.objects.create(
            user=user, table_name="test", name="My View", columns=["id"]
        )
        request = _make_request(
            rf,
            user=user,
            post_params={PROFILE_ACTION_PARAM: "save"},
        )
        # Set active profile and new column selection in session
        from rg.table.config import set_active_profile_info

        set_active_profile_info(request.session, "test", profile.pk, "My View")
        set_column_preference(request.session, "test", ["id", "name", "country"])

        table = ProfileTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)

        profile.refresh_from_db()
        assert profile.columns == ["id", "name", "country"]

    def test_delete_via_post(self, rf, data, user):
        """POST with _profile_action=delete removes the profile."""
        profile = TableProfile.objects.create(
            user=user, table_name="test", name="Delete Me"
        )
        request = _make_request(
            rf,
            user=user,
            post_params={
                PROFILE_ACTION_PARAM: "delete",
                PROFILE_ID_PARAM: str(profile.pk),
            },
        )
        # Set it as active so we can verify it gets cleared
        from rg.table.config import set_active_profile_info

        set_active_profile_info(request.session, "test", profile.pk, "Delete Me")

        table = ProfileTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)

        assert not TableProfile.objects.filter(pk=profile.pk).exists()
        assert get_active_profile_info(request.session, "test") is None

    def test_set_default_via_post(self, rf, data, user):
        """POST with _profile_action=set_default toggles default flag."""
        p1 = TableProfile.objects.create(
            user=user, table_name="test", name="A", is_default=True
        )
        p2 = TableProfile.objects.create(
            user=user, table_name="test", name="B"
        )
        request = _make_request(
            rf,
            user=user,
            post_params={
                PROFILE_ACTION_PARAM: "set_default",
                PROFILE_ID_PARAM: str(p2.pk),
            },
        )
        table = ProfileTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)

        p1.refresh_from_db()
        p2.refresh_from_db()
        assert p1.is_default is False
        assert p2.is_default is True

    def test_auto_load_default_profile(self, rf, data, user):
        """Default profile auto-loads on first visit for authenticated user."""
        TableProfile.objects.create(
            user=user,
            table_name="test",
            name="Default View",
            columns=["name", "population"],
            per_page=50,
            is_default=True,
        )
        request = _make_request(rf, user=user)
        table = ProfileTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)

        visible = [col.name for col in table.columns]
        assert visible == ["name", "population"]
        assert table.active_profile is not None
        assert table.active_profile["name"] == "Default View"

    def test_no_auto_load_when_active_profile_set(self, rf, data, user):
        """Default profile not loaded when an active profile is already set."""
        TableProfile.objects.create(
            user=user,
            table_name="test",
            name="Default View",
            columns=["population"],
            is_default=True,
        )
        request = _make_request(rf, user=user)
        from rg.table.config import set_active_profile_info

        set_active_profile_info(request.session, "test", 999, "Other")

        table = ProfileTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)

        # Should NOT have loaded default (all columns visible, not just population)
        visible = [col.name for col in table.columns]
        assert visible == ["id", "name", "country", "population"]

    def test_profiles_list_populated(self, rf, data, user):
        """profiles_list is populated for template use."""
        TableProfile.objects.create(user=user, table_name="test", name="A")
        TableProfile.objects.create(
            user=user, table_name="test", name="B", is_default=True
        )
        request = _make_request(rf, user=user)
        table = ProfileTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)

        assert len(table.profiles_list) == 2
        names = {p["name"] for p in table.profiles_list}
        assert names == {"A", "B"}

    def test_anonymous_user_no_profiles(self, rf, data):
        """Anonymous user: profiles_list empty, no profile UI data."""
        request = _make_request(rf)
        table = ProfileTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)

        assert table.profiles_list == []
        assert table.active_profile is None

    def test_anonymous_user_profile_action_ignored(self, rf, data):
        """Anonymous user: profile actions in POST are ignored."""
        request = _make_request(
            rf,
            post_params={
                PROFILE_ACTION_PARAM: "save_as",
                PROFILE_NAME_PARAM: "Should Not Create",
            },
        )
        table = ProfileTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)

        assert TableProfile.objects.count() == 0


# --- Per-page selection tests ---


class TestPerPageSelection:
    def test_per_page_from_post(self, rf, data):
        """POST with _per_page_submit stores per_page in session."""
        request = _make_request(
            rf,
            post_params={
                PER_PAGE_SUBMIT_PARAM: "1",
                PER_PAGE_VALUE_PARAM: "50",
            },
        )
        table = PerPageTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)

        assert get_per_page_preference(request.session, "test") == 50
        assert table.paginator.per_page == 50
        assert table.current_per_page == 50

    def test_per_page_from_session(self, rf, data):
        """Session per_page overrides paginate default."""
        request = _make_request(rf)
        set_per_page_preference(request.session, "test", 10)

        table = PerPageTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)

        assert table.paginator.per_page == 10
        assert table.current_per_page == 10

    def test_per_page_url_overrides_session(self, rf, data):
        """URL per_page param overrides session preference."""
        request = _make_request(rf, get_params={"per_page": "25"})
        set_per_page_preference(request.session, "test", 10)

        table = PerPageTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 50}).configure(table)

        assert table.paginator.per_page == 25

    def test_invalid_per_page_ignored(self, rf, data):
        """Invalid _per_page value in POST is ignored."""
        request = _make_request(
            rf,
            post_params={
                PER_PAGE_SUBMIT_PARAM: "1",
                PER_PAGE_VALUE_PARAM: "abc",
            },
        )
        table = PerPageTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)

        assert get_per_page_preference(request.session, "test") is None
        assert table.paginator.per_page == 25

    def test_disallowed_per_page_ignored(self, rf, data):
        """Per-page value not in choices is ignored."""
        request = _make_request(
            rf,
            post_params={
                PER_PAGE_SUBMIT_PARAM: "1",
                PER_PAGE_VALUE_PARAM: "999",
            },
        )
        table = PerPageTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)

        assert get_per_page_preference(request.session, "test") is None

    def test_current_per_page_set(self, rf, data):
        """current_per_page is set after configure."""
        request = _make_request(rf)
        table = PerPageTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)
        assert table.current_per_page == 25


# --- Template rendering tests ---


@pytest.mark.django_db
class TestProfileSelectorTemplate:
    def test_profile_selector_rendered_when_enabled(self, rf, data, user):
        """Profile selector appears when enable_profiles is True."""
        request = _make_request(rf, user=user)
        table = ProfileTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)

        html = render_to_string(
            table._meta.template_name,
            {"table": table, "request": request},
            request=request,
        )
        assert 'id="profile_sel_test"' in html
        assert "Profiles" in html

    def test_profile_selector_not_rendered_when_disabled(self, rf, data):
        """Profile selector not shown when enable_profiles is False."""
        request = _make_request(rf)
        table = NoProfileTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)

        html = render_to_string(
            table._meta.template_name,
            {"table": table, "request": request},
            request=request,
        )
        assert "profile_sel_" not in html

    def test_active_profile_name_shown(self, rf, data, user):
        """Active profile name shown in button when a profile is active."""
        TableProfile.objects.create(
            user=user,
            table_name="test",
            name="My View",
            columns=["id", "name"],
            is_default=True,
        )
        request = _make_request(rf, user=user)
        table = ProfileTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)

        html = render_to_string(
            table._meta.template_name,
            {"table": table, "request": request},
            request=request,
        )
        assert "My View" in html

    def test_profile_list_rendered(self, rf, data, user):
        """Each profile in profiles_list is rendered."""
        TableProfile.objects.create(user=user, table_name="test", name="View A")
        TableProfile.objects.create(user=user, table_name="test", name="View B")
        request = _make_request(rf, user=user)
        table = ProfileTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)

        html = render_to_string(
            table._meta.template_name,
            {"table": table, "request": request},
            request=request,
        )
        assert "View A" in html
        assert "View B" in html

    def test_save_as_input_present(self, rf, data, user):
        """Save-as text input is present in profile selector."""
        request = _make_request(rf, user=user)
        table = ProfileTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)

        html = render_to_string(
            table._meta.template_name,
            {"table": table, "request": request},
            request=request,
        )
        assert 'name="_profile_name"' in html
        assert "Save as..." in html

    def test_anonymous_no_profile_selector(self, rf, data):
        """Anonymous user sees no profile selector at all."""
        request = _make_request(rf)
        table = ProfileTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)

        html = render_to_string(
            table._meta.template_name,
            {"table": table, "request": request},
            request=request,
        )
        assert "profile_sel_test" not in html


class TestPerPageSelectorTemplate:
    def test_per_page_selector_rendered(self, rf, data):
        """Per-page selector rendered when enabled."""
        request = _make_request(rf)
        table = PerPageTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)

        html = render_to_string(
            table._meta.template_name,
            {"table": table, "request": request},
            request=request,
        )
        assert "Show:" in html
        assert 'name="_per_page_submit"' in html

    def test_per_page_choices_shown(self, rf, data):
        """Each per-page choice is rendered as a button."""
        request = _make_request(rf)
        table = PerPageTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)

        html = render_to_string(
            table._meta.template_name,
            {"table": table, "request": request},
            request=request,
        )
        for choice in (10, 25, 50):
            assert f'value="{choice}"' in html

    def test_per_page_not_rendered_when_disabled(self, rf, data):
        """Per-page selector not shown when disabled."""
        request = _make_request(rf)
        table = NoProfileTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)

        html = render_to_string(
            table._meta.template_name,
            {"table": table, "request": request},
            request=request,
        )
        assert "_per_page_submit" not in html


# --- Bulma template tests ---


@pytest.mark.django_db
class TestBulmaProfileTemplates:
    def test_profile_selector_rendered(self, rf, data, user):
        """Profile selector renders with Bulma classes."""

        class BulmaProfileTable(Table):
            id = tables.Column()
            name = tables.Column()

            class Meta(TableMeta):
                template_kit = "bulma"
                enable_profiles = True

        request = _make_request(rf, user=user)
        table = BulmaProfileTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)

        html = render_to_string(
            table._meta.template_name,
            {"table": table, "request": request},
            request=request,
        )
        assert "profile_sel_test" in html
        assert "dropdown-trigger" in html

    def test_per_page_selector_rendered(self, rf, data):
        """Per-page selector renders with Bulma classes."""

        class BulmaPerPageTable(Table):
            id = tables.Column()
            name = tables.Column()

            class Meta(TableMeta):
                template_kit = "bulma"
                enable_per_page_selection = True
                per_page_choices = (10, 25)

        request = _make_request(rf)
        table = BulmaPerPageTable(data, name="test")
        RequestConfig(request, paginate={"per_page": 25}).configure(table)

        html = render_to_string(
            table._meta.template_name,
            {"table": table, "request": request},
            request=request,
        )
        assert "Show:" in html
        assert "is-small" in html
