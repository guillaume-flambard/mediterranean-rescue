"""Private publication API (ADR 0013): prepare drafts and publish from the team space.
Synthetic inputs, real PostGIS."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client, override_settings

from catalog.crosswalk import approve_link
from catalog.models import Event, PublicationAudit
from catalog.tests.test_private_api import PrivateApiTestCase
from catalog.tests.test_sheets import ops_csv, ops_row


class PublicationApiTests(PrivateApiTestCase):
    def setUp(self):
        super().setUp()
        self.reviewer.user_permissions.add(
            Permission.objects.get(codename="add_event"),
            Permission.objects.get(codename="publish_event"),
        )
        self.reviewer = get_user_model().objects.get(pk=self.reviewer.pk)
        snapshot, _ = self.stage(
            ops_csv(
                ops_row(nb_survivor="42"),
                ops_row(date="04/02/2024", nb_survivor="7"),
                ops_row(date="05/02/2024", nb_survivor="3"),
            )
        )
        rows = list(snapshot.rows.order_by("line"))
        # Two rows verified, the third still waiting for a volunteer.
        for row in rows[:2]:
            approve_link(row=row, actor=self.reviewer, reason="Checked")

    def overview(self):
        return self.get("publication/").json()

    def test_overview_says_what_is_ready_and_who_may_do_what(self):
        body = self.overview()
        self.assertEqual(
            body["preparation"][0] | {"exported_at": None},
            {
                "sheet": "Data_operations",
                "exported_at": None,
                "ready": 2,
                "prepared": 0,
                "changed": 0,
                "not_verified": 1,
                "to_fix": 0,
            },
        )
        self.assertEqual(body["events"], {"draft": 0, "published": 0, "withdrawn": 0})
        self.assertEqual(body["can"], {"prepare": True, "publish": True})
        self.assertEqual(body["sources"], [{"name": self.source.name, "rights_approved": False}])

    def test_prepare_turns_verified_rows_into_private_drafts_with_a_reason(self):
        self.assertEqual(self.post("publication/prepare/", {"reason": ""}).status_code, 400)
        response = self.post("publication/prepare/", {"reason": "Checked on 24 October"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["created"], 2)
        self.assertEqual(response.json()["overview"]["events"]["draft"], 2)
        self.assertEqual(response.json()["overview"]["preparation"][0]["prepared"], 2)
        self.assertFalse(Event.objects.exclude(status="draft").exists())
        again = self.post("publication/prepare/", {"reason": "Again"}).json()
        self.assertEqual(again["created"], 0)

    # Fixture sources are synthetic: the public API shows them only in training mode.
    @override_settings(DATA_MODE="training")
    def test_publishing_waits_for_the_source_rights_then_records_who_and_why(self):
        self.post("publication/prepare/", {"reason": "Checked"})
        drafts = self.get("publication/events/?status=draft").json()
        self.assertEqual(drafts["total_count"], 2)
        ids = [item["id"] for item in drafts["items"]]
        self.assertFalse(drafts["items"][0]["rights_approved"])

        refused = self.post(
            "publication/decisions/", {"action": "publish", "events": ids, "reason": "Ready"}
        )
        self.assertEqual(refused.status_code, 409)
        self.assertEqual(refused.json()["code"], "rights_not_approved")
        self.assertFalse(Event.objects.filter(status="published").exists())

        self.source.rights_approved = True
        self.source.license_note = "Fictitious licence for tests"
        self.source.save()
        published = self.post(
            "publication/decisions/", {"action": "publish", "events": ids, "reason": "Ready"}
        )
        self.assertEqual(published.json(), {"action": "publish", "count": 2})
        self.assertEqual(Event.objects.filter(status="published").count(), 2)
        self.assertEqual(
            set(PublicationAudit.objects.values_list("reason", "actor__username")),
            {("Ready", "reviewer")},
        )
        self.assertEqual(self.client.get("/api/v1/events/").json()["total_count"], 2)

        # Publishing twice is refused; withdrawing removes it from the public site.
        again = self.post(
            "publication/decisions/", {"action": "publish", "events": ids[:1], "reason": "Again"}
        )
        self.assertEqual(again.status_code, 409)
        withdrawn = self.post(
            "publication/decisions/",
            {"action": "withdraw", "events": ids[:1], "reason": "Position to check"},
        )
        self.assertEqual(withdrawn.json()["count"], 1)
        self.assertEqual(self.client.get("/api/v1/events/").json()["total_count"], 1)
        self.assertEqual(self.overview()["events"], {"draft": 0, "published": 1, "withdrawn": 1})

    def test_one_refusal_publishes_nothing(self):
        self.post("publication/prepare/", {"reason": "Checked"})
        self.source.rights_approved = True
        self.source.license_note = "Fictitious licence for tests"
        self.source.save()
        ids = [str(event.pk) for event in Event.objects.all()]
        missing = "00000000-0000-0000-0000-000000000000"
        response = self.post(
            "publication/decisions/",
            {"action": "publish", "events": [*ids, missing], "reason": "Ready"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Event.objects.filter(status="published").exists())

    def test_permissions_are_checked_on_every_step(self):
        self.assertEqual(self.get("publication/", client=Client()).status_code, 401)
        outsider = Client()
        outsider.force_login(self.outsider)
        self.assertEqual(self.get("publication/", client=outsider).status_code, 403)

        reader = get_user_model().objects.create_user(username="reader", password=None)
        reader.user_permissions.add(Permission.objects.get(codename="review_identity"))
        client = Client(enforce_csrf_checks=True)
        client.force_login(reader)
        token = client.get("/api/csrf/").json()["csrfToken"]
        self.assertEqual(
            self.get("publication/", client=client).json()["can"],
            {"prepare": False, "publish": False},
        )
        for path, body in (
            ("publication/prepare/", {"reason": "x"}),
            (
                "publication/decisions/",
                {"action": "publish", "events": [str(self.source.pk)], "reason": "x"},
            ),
        ):
            response = client.post(
                f"/api/private/v1/{path}",
                data=body,
                content_type="application/json",
                HTTP_X_CSRFTOKEN=token,
            )
            self.assertEqual(response.status_code, 403, path)
        self.assertFalse(Event.objects.exists())
