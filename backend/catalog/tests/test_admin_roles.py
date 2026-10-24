"""Volunteer roles, the coordinator's limited user administration, the reason asked before an
admin publication and the platform settings hardened after the Django audit (ADR 0013)."""

from django.conf import settings
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.test import Client, TestCase

from catalog.models import Event, PublicationAudit, Source

User = get_user_model()


class RoleTests(TestCase):
    def test_each_role_is_a_group_with_exactly_its_permission(self):
        expected = {
            "Verify events": {"catalog.review_identity"},
            "Prepare events": {"catalog.add_event"},
            "Publish events": {"catalog.publish_event"},
            "Manual import": {"catalog.add_sheetsnapshot"},
            "Coordinator": {
                "auth.view_user",
                "auth.add_user",
                "auth.change_user",
                "auth.view_group",
            },
        }
        for name, permissions in expected.items():
            group = Group.objects.get(name=name)
            found = {
                f"{permission.content_type.app_label}.{permission.codename}"
                for permission in group.permissions.select_related("content_type")
            }
            self.assertEqual(found, permissions, name)

    def test_a_volunteer_with_a_role_gets_its_permission(self):
        volunteer = User.objects.create_user(username="volunteer", password=None)
        volunteer.groups.add(Group.objects.get(name="Publish events"))
        volunteer = User.objects.get(pk=volunteer.pk)
        self.assertTrue(volunteer.has_perm("catalog.publish_event"))
        self.assertFalse(volunteer.has_perm("catalog.review_identity"))


class CoordinatorTests(TestCase):
    def setUp(self):
        self.coordinator = User.objects.create_user(
            username="coordinator", password=None, is_staff=True
        )
        self.coordinator.groups.add(Group.objects.get(name="Coordinator"))
        self.volunteer = User.objects.create_user(username="volunteer", password=None)
        self.lead = User.objects.create_superuser(username="lead", password=None)
        self.client = Client()
        self.client.force_login(self.coordinator)

    def test_sees_volunteers_only_and_cannot_open_staff_accounts(self):
        page = self.client.get("/admin/auth/user/")
        self.assertContains(page, "volunteer")
        self.assertNotContains(page, ">lead<")
        # A staff account is outside the coordinator's list: the admin answers as for a missing one.
        self.assertEqual(
            self.client.get(f"/admin/auth/user/{self.lead.pk}/change/").status_code, 302
        )

    def test_can_give_volunteer_roles_but_not_coordinator_or_staff(self):
        url = f"/admin/auth/user/{self.volunteer.pk}/change/"
        form = self.client.get(url)
        self.assertNotContains(form, 'name="is_staff"')
        self.assertNotContains(form, 'name="user_permissions"')
        verify = Group.objects.get(name="Verify events")
        coordinator = Group.objects.get(name="Coordinator")
        base = {
            "username": "volunteer",
            "first_name": "",
            "last_name": "",
            "email": "",
            "is_active": "on",
        }
        refused = self.client.post(url, {**base, "groups": [coordinator.pk], "is_staff": "on"})
        self.assertEqual(refused.status_code, 200)  # form shown again with the invalid choice
        self.assertFalse(User.objects.get(pk=self.volunteer.pk).groups.exists())
        saved = self.client.post(url, {**base, "groups": [verify.pk], "is_staff": "on"})
        self.assertEqual(saved.status_code, 302)
        volunteer = User.objects.get(pk=self.volunteer.pk)
        self.assertEqual(list(volunteer.groups.all()), [verify])
        self.assertFalse(volunteer.is_staff)


class AdminPublicationReasonTests(TestCase):
    def setUp(self):
        self.source = Source.objects.create(
            key="fixture",
            name="Fictitious source",
            url="https://example.org",
            synthetic=True,
            rights_approved=True,
            license_note="Fictitious licence for tests",
        )
        self.event = Event.objects.create(
            source=self.source,
            external_id="e1",
            kind="rescue",
            occurred_on="2024-02-03",
            title="Fictitious rescue",
            source_url="https://example.org/e1",
        )
        self.lead = User.objects.create_superuser(username="lead", password=None)
        self.client = Client()
        self.client.force_login(self.lead)

    def test_publishing_in_the_admin_asks_for_a_reason_and_records_it(self):
        action = {"action": "publish_reviewed", ACTION_CHECKBOX_NAME: [str(self.event.pk)]}
        asked = self.client.post("/admin/catalog/event/", action)
        self.assertContains(asked, 'name="reason"')
        self.assertEqual(Event.objects.get(pk=self.event.pk).status, "draft")
        empty = self.client.post("/admin/catalog/event/", {**action, "apply": "1", "reason": " "})
        self.assertContains(empty, 'name="reason"')
        self.client.post(
            "/admin/catalog/event/", {**action, "apply": "1", "reason": "Checked with SOS"}
        )
        self.assertEqual(Event.objects.get(pk=self.event.pk).status, "published")
        self.assertEqual(PublicationAudit.objects.get().reason, "Checked with SOS")


class ConstraintTests(TestCase):
    def test_the_database_refuses_what_the_forms_refuse(self):
        source = Source.objects.create(key="s", name="S", url="https://example.org")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Source.objects.filter(pk=source.pk).update(rights_approved=True, license_note=" ")
        base = {
            "source": source,
            "kind": "rescue",
            "occurred_on": "2024-02-03",
            "title": "Fictitious",
            "source_url": "https://example.org",
        }
        with self.assertRaises(IntegrityError), transaction.atomic():
            Event.objects.create(**{**base, "kind": "invented"}, external_id="a")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Event.objects.create(**base, external_id="b", location_precision="reported")


class PlatformSettingsTests(TestCase):
    def test_proxies_and_shared_cache(self):
        # X-Forwarded-For is ignored unless the deployment declares its proxies.
        self.assertEqual(settings.REST_FRAMEWORK["NUM_PROXIES"], 0)
        self.assertEqual(
            settings.CACHES["default"]["BACKEND"], "django.core.cache.backends.db.DatabaseCache"
        )
        cache.set("probe", "value")
        self.assertEqual(cache.get("probe"), "value")
        self.assertTrue(settings.DATABASES["default"]["CONN_HEALTH_CHECKS"])

    def test_the_administration_speaks_french_when_asked(self):
        lead = User.objects.create_superuser(username="lead", password=None)
        client = Client(HTTP_ACCEPT_LANGUAGE="fr")
        client.force_login(lead)
        self.assertContains(client.get("/admin/"), "Administration de Mediterranean Rescue")
        english = Client(HTTP_ACCEPT_LANGUAGE="en")
        english.force_login(lead)
        self.assertContains(english.get("/admin/"), "Mediterranean Rescue administration")
        self.assertEqual(Permission.objects.filter(codename="publish_event").count(), 1)
