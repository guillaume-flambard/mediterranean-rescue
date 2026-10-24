"""Private review API (ADR 0009): sessions, CSRF, permissions, errors and decisions."""

import json
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client, override_settings

from catalog.crosswalk import approve_link
from catalog.models import Event, RowIdentityLink, SourceIdentity
from catalog.tests.test_crosswalk import CrosswalkTestCase
from catalog.tests.test_sheets import ops_csv, ops_row

BASE = "/api/private/v1"


@override_settings(SECURE_SSL_REDIRECT=False, SESSION_COOKIE_SECURE=False, CSRF_COOKIE_SECURE=False)
class PrivateApiTestCase(CrosswalkTestCase):
    def setUp(self):
        super().setUp()
        self.reviewer.is_staff = True
        self.reviewer.save()
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(self.reviewer)
        self.token = self.client.get("/api/csrf/").json()["csrfToken"]

    def post(self, path, body, token=True, client=None):
        headers = {"HTTP_X_CSRFTOKEN": self.token} if token else {}
        return (client or self.client).post(
            f"{BASE}/{path}", data=json.dumps(body), content_type="application/json", **headers
        )

    def get(self, path, client=None):
        return (client or self.client).get(f"{BASE}/{path}")


class AccessTests(PrivateApiTestCase):
    def test_anonymous_gets_401_with_a_code(self):
        response = self.get("me/", client=Client())
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["code"], "not_authenticated")

    def test_missing_permission_is_403_not_an_empty_result(self):
        outsider = Client()
        outsider.force_login(self.outsider)
        snapshot, _ = self.stage(ops_csv(ops_row()))
        for path in (
            "snapshots/",
            f"review/rows/?snapshot={snapshot.pk}",
            f"review/rows/{snapshot.rows.get().pk}/",
        ):
            response = self.get(path, client=outsider)
            self.assertEqual(response.status_code, 403, path)
            self.assertEqual(response.json()["code"], "permission_denied")

    def test_me_lists_useful_permissions_and_is_never_cached(self):
        response = self.get("me/")
        self.assertEqual(
            response.json(),
            {
                "username": "reviewer",
                "permissions": {
                    "review_identity": True,
                    "stage_snapshot": True,
                    "prepare_drafts": False,
                    "publish": False,
                },
            },
        )
        self.assertEqual(response["Cache-Control"], "no-store")

    def test_writes_require_the_csrf_token(self):
        snapshot, _ = self.stage(ops_csv(ops_row()))
        row = snapshot.rows.get()
        response = self.post(
            f"review/rows/{row.pk}/decision/",
            {"action": "create_identity", "reason": "r"},
            token=False,
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["code"], "csrf_failed")
        self.assertFalse(RowIdentityLink.objects.exists())

    def test_public_api_is_unchanged(self):
        response = Client().get("/api/v1/events/?kind=nope")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "http_400")

    def test_unknown_parameters_and_methods(self):
        self.assertEqual(self.get("snapshots/?evil=1").json()["code"], "invalid")
        response = self.client.delete(f"{BASE}/me/", HTTP_X_CSRFTOKEN=self.token)
        self.assertEqual(
            (response.status_code, response.json()["code"]), (405, "method_not_allowed")
        )


class QueueTests(PrivateApiTestCase):
    def test_snapshots_are_listed_newest_first(self):
        older, _ = self.stage(ops_csv(ops_row()))
        newer, _ = self.stage(ops_csv(ops_row(date="04/02/2024")))
        items = self.get("snapshots/").json()["items"]
        self.assertEqual([item["id"] for item in items], [str(newer.pk), str(older.pk)])
        self.assertEqual(items[0]["source"], {"key": "fixture", "name": "Synthetic fixture"})
        self.assertEqual(items[0]["row_count"], 1)

    def test_queue_facets_are_exclusive_and_paginated(self):
        snapshot, _ = self.stage(
            ops_csv(
                *(ops_row(date=f"{day:02d}/02/2024") for day in range(1, 28)),
                ops_row(date="31/02/2024"),
            )
        )
        approve_link(row=snapshot.rows.get(line=2), actor=self.reviewer, reason="r")
        page = self.get(f"review/rows/?snapshot={snapshot.pk}").json()
        self.assertEqual(page["counts"], {"to_review": 26, "blocked": 1, "linked": 1})
        self.assertEqual(
            (page["total_count"], len(page["items"]), page["has_next"]), (26, 25, True)
        )
        first = page["items"][0]
        self.assertEqual(
            {
                key: first[key]
                for key in ("line", "status", "proposal", "occurred_on", "kind", "people")
            },
            {
                "line": 3,
                "status": "to_review",
                "proposal": "new",
                "occurred_on": "2024-02-02",
                "kind": "rescue",
                "people": None,
            },
        )
        blocked = self.get(f"review/rows/?snapshot={snapshot.pk}&status=blocked").json()["items"]
        self.assertEqual(
            [(item["line"], item["error_codes"]) for item in blocked], [(29, ["impossible_date"])]
        )
        self.assertEqual(
            self.get(f"review/rows/?snapshot={snapshot.pk}&status=linked").json()["total_count"], 1
        )

    def test_queue_needs_a_valid_snapshot(self):
        self.assertEqual(self.get("review/rows/").json()["code"], "invalid")
        missing = self.get("review/rows/?snapshot=00000000-0000-0000-0000-000000000000")
        self.assertEqual((missing.status_code, missing.json()["code"]), (404, "not_found"))


class RowTests(PrivateApiTestCase):
    def test_row_shows_received_interpreted_and_candidates(self):
        first, _ = self.stage(ops_csv(ops_row(nb_survivor="40")))
        link = approve_link(row=first.rows.get(), actor=self.reviewer, reason="r")
        corrected, _ = self.stage(ops_csv(ops_row(nb_survivor="42")))
        row = corrected.rows.get()
        body = self.get(f"review/rows/{row.pk}/").json()
        self.assertEqual(body["snapshot"]["id"], str(corrected.pk))
        self.assertEqual(body["line"], 2)
        received = dict(zip(body["received"]["headers"], body["received"]["cells"]))
        self.assertEqual(received["nb_survivor"], "42")
        self.assertEqual(body["interpreted"]["nb_survivor"], 42)
        self.assertEqual(body["proposal"]["kind"], "candidates")
        (candidate,) = body["proposal"]["candidates"]
        self.assertEqual(candidate["id"], str(link.identity_id))
        self.assertEqual(candidate["summary"]["people"], 40)
        self.assertIsNone(body["decision"])

    def test_linked_row_shows_its_decision(self):
        snapshot, _ = self.stage(ops_csv(ops_row()))
        row = snapshot.rows.get()
        approve_link(row=row, actor=self.reviewer, reason="First observation")
        decision = self.get(f"review/rows/{row.pk}/").json()["decision"]
        self.assertEqual(
            {key: decision[key] for key in ("match", "approved_by", "reason")},
            {"match": "new", "approved_by": "reviewer", "reason": "First observation"},
        )


class DecisionTests(PrivateApiTestCase):
    def test_create_identity(self):
        snapshot, _ = self.stage(ops_csv(ops_row()))
        row = snapshot.rows.get()
        response = self.post(
            f"review/rows/{row.pk}/decision/", {"action": "create_identity", "reason": "New rescue"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["decision"]["match"], "new")
        self.assertEqual(SourceIdentity.objects.count(), 1)
        self.assertEqual(Event.objects.count(), 0)

    def test_link_is_recorded_as_a_reviewed_match(self):
        first, _ = self.stage(ops_csv(ops_row(nb_survivor="40")))
        link = approve_link(row=first.rows.get(), actor=self.reviewer, reason="r")
        corrected, _ = self.stage(ops_csv(ops_row(nb_survivor="42")))
        response = self.post(
            f"review/rows/{corrected.rows.get().pk}/decision/",
            {"action": "link", "identity": str(link.identity_id), "reason": "Count corrected"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["decision"]["match"], "reviewed_match")

    def test_invalid_input_is_400_with_field_errors(self):
        snapshot, _ = self.stage(ops_csv(ops_row()))
        row = snapshot.rows.get()
        for body in (
            {"action": "create_identity", "reason": "  "},
            {"action": "link", "reason": "r"},
            {"action": "approve_everything", "reason": "r"},
        ):
            response = self.post(f"review/rows/{row.pk}/decision/", body)
            self.assertEqual(
                (response.status_code, response.json()["code"]), (400, "invalid"), body
            )
        self.assertFalse(RowIdentityLink.objects.exists())

    def test_state_changes_are_409_conflicts(self):
        snapshot, _ = self.stage(ops_csv(ops_row(), ops_row(date="31/02/2024")))
        sane, broken = snapshot.rows.order_by("line")
        approve_link(row=sane, actor=self.reviewer, reason="Another reviewer")
        again = self.post(
            f"review/rows/{sane.pk}/decision/", {"action": "create_identity", "reason": "r"}
        )
        self.assertEqual((again.status_code, again.json()["code"]), (409, "conflict"))
        blocked = self.post(
            f"review/rows/{broken.pk}/decision/", {"action": "create_identity", "reason": "r"}
        )
        self.assertEqual((blocked.status_code, blocked.json()["code"]), (409, "conflict"))
        self.assertNotIn("31/02/2024", blocked.content.decode())

    def test_permission_is_rechecked_on_write(self):
        Permission.objects.get(codename="review_identity").user_set.remove(self.reviewer)
        snapshot, _ = self.stage(ops_csv(ops_row()))
        response = self.post(
            f"review/rows/{snapshot.rows.get().pk}/decision/",
            {"action": "create_identity", "reason": "r"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(RowIdentityLink.objects.exists())


class ExactCarryTests(PrivateApiTestCase):
    def setUp(self):
        super().setUp()
        first, _ = self.stage(ops_csv(ops_row(), ops_row(date="04/02/2024")))
        for row in first.rows.all():
            approve_link(row=row, actor=self.reviewer, reason="Initial")
        self.second, _ = self.stage(
            ops_csv(ops_row(date="04/02/2024"), ops_row(), ops_row(date="09/02/2024"))
        )

    def test_only_selected_eligible_rows_are_carried(self):
        carry = self.second.rows.get(line=2)
        response = self.post(
            f"review/snapshots/{self.second.pk}/exact-carries/",
            {"rows": [str(carry.pk)], "reason": "Unchanged"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"carried": 1})
        self.assertTrue(RowIdentityLink.objects.filter(row=carry, match="exact_carry").exists())
        self.assertFalse(RowIdentityLink.objects.filter(row__line=3, snapshot=self.second).exists())

    def test_an_ineligible_row_refuses_the_whole_selection(self):
        rows = [str(self.second.rows.get(line=line).pk) for line in (2, 4)]
        response = self.post(
            f"review/snapshots/{self.second.pk}/exact-carries/",
            {"rows": rows, "reason": "Unchanged"},
        )
        self.assertEqual((response.status_code, response.json()["code"]), (409, "conflict"))
        self.assertFalse(RowIdentityLink.objects.filter(snapshot=self.second).exists())


class IdentitySearchTests(PrivateApiTestCase):
    def test_identities_of_the_same_source_and_sheet_by_date(self):
        snapshot, _ = self.stage(ops_csv(ops_row(), ops_row(date="10/03/2024")))
        for row in snapshot.rows.all():
            approve_link(row=row, actor=self.reviewer, reason="r")
        other, _ = self.stage(ops_csv(ops_row()), source=self.other_source)
        approve_link(row=other.rows.get(), actor=self.reviewer, reason="r")
        items = self.get(f"review/identities/?snapshot={snapshot.pk}&q=2024-03").json()["items"]
        self.assertEqual([item["summary"]["occurred_on"] for item in items], ["2024-03-10"])
        everything = self.get(f"review/identities/?snapshot={snapshot.pk}").json()["items"]
        self.assertEqual(len(everything), 2)


class SignInTests(PrivateApiTestCase):
    def setUp(self):
        super().setUp()
        self.reviewer.set_password("correct horse battery staple")
        self.reviewer.save()
        self.anonymous = Client(enforce_csrf_checks=True)
        self.anonymous_token = self.anonymous.get("/api/csrf/").json()["csrfToken"]

    def sign_in(self, username, password, token=True):
        headers = {"HTTP_X_CSRFTOKEN": self.anonymous_token} if token else {}
        return self.anonymous.post(
            f"{BASE}/session/",
            data=json.dumps({"username": username, "password": password}),
            content_type="application/json",
            **headers,
        )

    def test_sign_in_opens_a_session_and_sign_out_closes_it(self):
        response = self.sign_in("reviewer", "correct horse battery staple")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "reviewer")
        self.assertEqual(self.anonymous.get(f"{BASE}/me/").status_code, 200)
        token = self.anonymous.get("/api/csrf/").json()["csrfToken"]
        self.assertEqual(
            self.anonymous.delete(f"{BASE}/session/", HTTP_X_CSRFTOKEN=token).status_code, 204
        )
        self.assertEqual(self.anonymous.get(f"{BASE}/me/").status_code, 401)

    def test_failures_share_one_message(self):
        inactive = get_user_model().objects.create_user(username="gone", password="x")
        inactive.is_active = False
        inactive.save()
        bodies = [
            self.sign_in("reviewer", "wrong").json(),
            self.sign_in("nobody", "wrong").json(),
            self.sign_in("gone", "x").json(),
        ]
        self.assertEqual({body["code"] for body in bodies}, {"invalid_credentials"})
        self.assertEqual(len({body["detail"] for body in bodies}), 1)

    def test_sign_in_requires_the_csrf_token(self):
        response = self.sign_in("reviewer", "correct horse battery staple", token=False)
        self.assertEqual((response.status_code, response.json()["code"]), (403, "csrf_failed"))
        self.assertEqual(self.anonymous.get(f"{BASE}/me/").status_code, 401)

    def test_sign_in_attempts_are_rate_limited(self):
        from django.core.cache import cache
        from rest_framework.throttling import ScopedRateThrottle

        cache.clear()
        # DRF reads the rates when the class is defined: patch them on the class.
        with mock.patch.object(ScopedRateThrottle, "THROTTLE_RATES", {"sign_in": "2/min"}):
            self.sign_in("reviewer", "wrong")
            self.sign_in("reviewer", "wrong")
            response = self.sign_in("reviewer", "correct horse battery staple")
        cache.clear()
        self.assertEqual((response.status_code, response.json()["code"]), (429, "throttled"))


class ReviewScopeTests(PrivateApiTestCase):
    def test_port_snapshots_are_not_identity_review_and_404_names_nothing(self):
        from catalog.tests.test_crosswalk import ports_csv

        ports, _ = self.stage(ports_csv("Port fictif A,36° 48.0,10° 12.0"), sheet="Data_ports")
        events, _ = self.stage(ops_csv(ops_row()))
        self.assertEqual(
            [item["id"] for item in self.get("snapshots/").json()["items"]], [str(events.pk)]
        )
        self.assertEqual(self.get(f"review/rows/?snapshot={ports.pk}").json()["code"], "invalid")
        missing = self.get("review/rows/00000000-0000-0000-0000-000000000000/").json()
        self.assertEqual(missing, {"code": "not_found", "detail": "Not found."})
