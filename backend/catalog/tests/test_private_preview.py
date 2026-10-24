"""Private preview of the latest exports (ADR 0011): read-only, reviewers only."""

from django.test import Client

from catalog.models import Event
from catalog.tests.test_private_api import PrivateApiTestCase
from catalog.tests.test_sheets import ops_csv, ops_row


class PreviewTests(PrivateApiTestCase):
    def setUp(self):
        super().setUp()
        self.stage(
            ops_csv(
                ops_row(nb_survivor="42", Port_disembarkation="Port fictif"),
                ops_row(date="04/02/2024", nb_survivor="-1"),
                ops_row(date="05/02/2024", latitude="", longitude=""),
            )
        )

    def test_latest_rows_are_listed_with_their_review_state(self):
        body = self.get("preview/events/").json()
        self.assertEqual(body["total_count"], 3)
        self.assertEqual(body["counts"], {"to_review": 2, "blocked": 1, "linked": 0})
        self.assertEqual(
            [item["occurred_on"] for item in body["items"]],
            ["2024-02-05", "2024-02-04", "2024-02-03"],
        )
        last = body["items"][2]
        self.assertEqual(
            (last["people"], last["port_label"], last["status"]), (42, "Port fictif", "to_review")
        )
        self.assertEqual(body["items"][1]["status"], "blocked")
        self.assertFalse(Event.objects.exists())

    def test_filters_and_map_points(self):
        body = self.get("preview/events/?start=2024-02-04&status=to_review").json()
        self.assertEqual([item["occurred_on"] for item in body["items"]], ["2024-02-05"])
        points = self.get("preview/map-points/").json()
        self.assertEqual(points["located_count"], 2)
        self.assertEqual({point["status"] for point in points["points"]}, {"to_review", "blocked"})
        self.assertEqual(
            self.get("preview/events/?start=2024-03-01&end=2024-01-01").status_code, 400
        )

    def test_words_search_the_port_as_written(self):
        body = self.get("preview/events/?q=fictif").json()
        self.assertEqual([item["port_label"] for item in body["items"]], ["Port fictif"])
        self.assertEqual(self.get("preview/events/?q=nowhere").json()["total_count"], 0)

    def test_only_the_latest_export_is_previewed(self):
        old_row = self.get("preview/events/").json()["items"][0]["id"]
        self.stage(ops_csv(ops_row(date="06/02/2024")))
        body = self.get("preview/events/").json()
        self.assertEqual([item["occurred_on"] for item in body["items"]], ["2024-02-06"])
        self.assertEqual(self.get(f"preview/events/{body['items'][0]['id']}/").status_code, 200)
        self.assertEqual(self.get(f"preview/events/{old_row}/").status_code, 404)

    def test_reviewers_only(self):
        self.assertEqual(self.get("preview/events/", client=Client()).status_code, 401)
        outsider = Client()
        outsider.force_login(self.outsider)
        self.assertEqual(self.get("preview/map-points/", client=outsider).status_code, 403)
