"""The team's decisions, newest first, with who, when and why. Fictitious data."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import Client

from catalog.crosswalk import approve_link
from catalog.tests.test_private_api import PrivateApiTestCase
from catalog.tests.test_sheets import ops_csv, ops_row

User = get_user_model()


class HistoryTests(PrivateApiTestCase):
    def setUp(self):
        super().setUp()
        self.reviewer.user_permissions.add(
            Permission.objects.get(codename="add_event"),
            Permission.objects.get(codename="publish_event"),
        )
        self.reviewer = User.objects.get(pk=self.reviewer.pk)
        self.colleague = User.objects.create_user(username="colleague", password=None)
        self.colleague.groups.add(Group.objects.get(name="Verify events"))
        snapshot, _ = self.stage(
            ops_csv(ops_row(nb_survivor="42"), ops_row(date="04/02/2024", nb_survivor="7"))
        )
        first, second = snapshot.rows.order_by("line")
        approve_link(row=first, actor=self.reviewer, reason="Matches the sentence")
        approve_link(row=second, actor=self.colleague, reason="Checked by a colleague")
        self.snapshot, self.first = snapshot, first
        self.post("publication/prepare/", {"reason": "Ready for the map"})

    def test_mine_lists_my_decisions_newest_first_with_reason_and_link(self):
        items = self.get("history/").json()["items"]
        self.assertEqual([item["kind"] for item in items], ["prepare", "prepare", "verify"])
        verify = items[-1]
        self.assertEqual(
            {key: verify[key] for key in ("actor", "reason", "detail")},
            {"actor": "reviewer", "reason": "Matches the sentence", "detail": "new"},
        )
        self.assertEqual(verify["subject"]["occurred_on"], "2024-02-03")
        self.assertEqual(verify["subject"]["people"], 42)
        self.assertEqual(
            verify["path"], f"/workspace/review/{self.snapshot.pk}/rows/{self.first.pk}"
        )
        self.assertEqual(items[0]["reason"], "Ready for the map")

    def test_the_team_sees_everyones_decisions_and_can_filter_by_kind(self):
        verifications = self.get("history/?scope=team&kind=verify").json()["items"]
        self.assertEqual(
            sorted((item["actor"], item["reason"]) for item in verifications),
            [("colleague", "Checked by a colleague"), ("reviewer", "Matches the sentence")],
        )
        page = self.get("history/?scope=team&limit=1").json()
        self.assertEqual(len(page["items"]), 1)
        self.assertTrue(page["has_next"])

    def test_a_colleague_sees_their_own_only_in_mine(self):
        client = Client()
        client.force_login(self.colleague)
        mine = client.get("/api/private/v1/history/").json()["items"]
        self.assertEqual(
            [(item["kind"], item["actor"]) for item in mine], [("verify", "colleague")]
        )

    def test_only_team_members_read_it(self):
        self.assertEqual(Client().get("/api/private/v1/history/").status_code, 401)
        outsider = Client()
        outsider.force_login(self.outsider)
        self.assertEqual(outsider.get("/api/private/v1/history/").status_code, 403)
