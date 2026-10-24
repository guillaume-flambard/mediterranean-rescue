"""Private import and port reading API (ADR 0010)."""

from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from rest_framework.throttling import ScopedRateThrottle

from catalog.models import Event, Port, PortAlias, SheetSnapshot, Vessel
from catalog.private_ports import label_id
from catalog.tests.test_crosswalk import ports_csv
from catalog.tests.test_private_api import BASE, PrivateApiTestCase
from catalog.tests.test_sheets import ops_csv, ops_row


class ImportApiTestCase(PrivateApiTestCase):
    def upload(self, path, content, sheet="Data_operations", source=None, token=True):
        headers = {"HTTP_X_CSRFTOKEN": self.token} if token else {}
        return self.client.post(
            f"{BASE}/{path}",
            data={
                "source": str((source or self.source).pk),
                "sheet": sheet,
                "file": SimpleUploadedFile("export.csv", content, content_type="text/csv"),
            },
            **headers,
        )


class ImportTests(ImportApiTestCase):
    def test_options_list_sources_sheets_and_size_limit(self):
        body = self.get("imports/options/").json()
        self.assertEqual(body["sheets"], ["Data_operations", "Other_data", "Data_ports"])
        self.assertEqual(body["max_bytes"], 5242880)
        self.assertIn("Synthetic fixture", [source["name"] for source in body["sources"]])

    def test_me_tells_whether_the_user_may_add_an_export(self):
        self.assertTrue(self.get("me/").json()["permissions"]["stage_snapshot"])

    def test_diagnose_reports_without_writing_or_leaking_values(self):
        content = ops_csv(ops_row(Port_disembarkation="Port secret"), ops_row(nb_survivor="-1"))
        response = self.upload("imports/diagnose/", content)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["source_read"], "complete")
        self.assertTrue(body["stageable"])
        self.assertIsNone(body["existing_snapshot"])
        self.assertEqual(body["counts"]["rows_with_errors"], 1)
        self.assertIn(
            {"code": "negative_count", "severity": "error", "count": 1}, body["issues_by_code"]
        )
        self.assertEqual(body["issues"][0]["line"], 3)
        self.assertNotIn("Port secret", response.content.decode())
        self.assertFalse(SheetSnapshot.objects.exists())

    def test_cut_file_cannot_be_staged_and_says_why(self):
        content = ops_csv(ops_row()) + b'"unterminated'
        body = self.upload("imports/diagnose/", content).json()
        self.assertFalse(body["stageable"])
        self.assertIn(body["blocking_reason"], ("read_partial", "read_rejected"))
        response = self.upload("imports/", content)
        self.assertEqual(response.status_code, 400)
        self.assertIn("file", response.json()["errors"])
        self.assertFalse(SheetSnapshot.objects.exists())

    def test_staging_is_idempotent_and_diagnose_then_points_to_it(self):
        content = ops_csv(ops_row(), ops_row(date="04/02/2024"))
        first = self.upload("imports/", content)
        self.assertEqual(first.status_code, 201)
        snapshot = first.json()["snapshot"]
        self.assertTrue(first.json()["created"])
        self.assertEqual(snapshot["review"], {"to_review": 2, "blocked": 0, "linked": 0})
        self.assertEqual(snapshot["staged_by"], "reviewer")
        again = self.upload("imports/", content)
        self.assertEqual((again.status_code, again.json()["created"]), (200, False))
        self.assertEqual(again.json()["snapshot"]["id"], snapshot["id"])
        diagnosed = self.upload("imports/diagnose/", content).json()
        self.assertEqual(diagnosed["existing_snapshot"], snapshot["id"])
        self.assertEqual(SheetSnapshot.objects.count(), 1)
        self.assertFalse(Event.objects.exists())

    def test_list_and_detail_cover_every_sheet(self):
        self.upload("imports/", ports_csv("Port fictif A,36° 48.0,10° 12.0"), sheet="Data_ports")
        self.upload("imports/", ops_csv(ops_row(nb_survivor="-1")))
        items = self.get("imports/").json()["items"]
        self.assertEqual([item["sheet"] for item in items], ["Data_operations", "Data_ports"])
        detail = self.get(f"imports/{items[0]['id']}/").json()
        self.assertEqual(detail["rows_with_errors"], 1)
        self.assertEqual(detail["errors_by_code"], [{"code": "negative_count", "rows": 1}])
        self.assertIsNone(self.get(f"imports/{items[1]['id']}/").json()["review"])

    def test_writes_need_csrf_permission_and_a_known_source(self):
        content = ops_csv(ops_row())
        response = self.upload("imports/", content, token=False)
        self.assertEqual(response.json()["code"], "csrf_failed")
        outsider = Client(enforce_csrf_checks=True)
        outsider.force_login(self.outsider)
        token = outsider.get("/api/csrf/").json()["csrfToken"]
        response = outsider.post(
            f"{BASE}/imports/diagnose/",
            data={"source": str(self.source.pk), "sheet": "Data_operations"},
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.json()["code"], "permission_denied")
        response = self.client.post(
            f"{BASE}/imports/diagnose/",
            data={
                "source": "00000000-0000-0000-0000-000000000000",
                "sheet": "Data_operations",
                "file": SimpleUploadedFile("x.csv", content),
            },
            HTTP_X_CSRFTOKEN=self.token,
        )
        self.assertEqual(response.json()["errors"], {"source": ["Unknown source."]})

    def test_oversized_file_is_refused_before_reading(self):
        with mock.patch("catalog.private_imports.load_contract") as contract:
            contract.return_value = {"input": {"max_bytes": 10}, "sheets": {}}
            response = self.upload("imports/diagnose/", ops_csv(ops_row()))
        self.assertEqual(response.status_code, 400)
        self.assertIn("file", response.json()["errors"])

    def test_imports_are_rate_limited(self):
        with mock.patch.object(ScopedRateThrottle, "THROTTLE_RATES", {"imports": "1/min"}):
            self.upload("imports/diagnose/", ops_csv(ops_row()))
            response = self.upload("imports/diagnose/", ops_csv(ops_row()))
        self.assertEqual((response.status_code, response.json()["code"]), (429, "throttled"))


class ImportLimitTests(ImportApiTestCase):
    def user_with(self, codename):
        user = get_user_model().objects.create_user(username=codename, password=None)
        user.user_permissions.add(Permission.objects.get(codename=codename))
        client = Client(enforce_csrf_checks=True)
        client.force_login(user)
        return client, client.get("/api/csrf/").json()["csrfToken"]

    def test_each_permission_opens_only_its_part(self):
        reviewer, token = self.user_with("review_identity")
        response = reviewer.post(
            f"{BASE}/imports/",
            data={"source": str(self.source.pk), "sheet": "Data_operations"},
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(reviewer.get(f"{BASE}/imports/").status_code, 200)
        stager, _ = self.user_with("add_sheetsnapshot")
        self.assertEqual(stager.get(f"{BASE}/ports/labels/").status_code, 403)
        self.assertEqual(stager.get(f"{BASE}/imports/options/").status_code, 200)

    def test_a_real_sized_export_goes_through_and_a_larger_body_is_refused_early(self):
        content = ops_csv(*[ops_row(boat_type="x" * 200) for _ in range(400)])
        self.assertGreater(len(content), 65536)
        self.assertEqual(self.upload("imports/diagnose/", content).status_code, 200)
        response = self.client.post(
            f"{BASE}/imports/diagnose/",
            data=b"x",
            content_type="multipart/form-data; boundary=x",
            CONTENT_LENGTH=str(5242880 + 65536 + 1),
            HTTP_X_CSRFTOKEN=self.token,
        )
        self.assertEqual(response.status_code, 413)
        # Other API routes keep the small limit.
        response = self.client.post(
            f"{BASE}/session/",
            data=b"{" + b" " * 70000 + b"}",
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.token,
        )
        self.assertEqual(response.status_code, 413)


class PortLabelTests(PrivateApiTestCase):
    def setUp(self):
        super().setUp()
        self.stage(
            ops_csv(
                ops_row(Port_disembarkation="Port fictif A"),
                ops_row(date="04/02/2024", Port_disembarkation="Port fictif A"),
                ops_row(date="05/02/2024", Port_disembarkation="Port fictif B"),
                ops_row(date="06/02/2024", Port_disembarkation="Navire fictif"),
            )
        )
        self.stage(
            ports_csv("Port fictif A,36° 48.0,10° 12.0", "Port fictif B,39° 26.32,0° 18.59"),
            sheet="Data_ports",
        )

    def labels(self, status="to_read"):
        return self.get(f"ports/labels/?status={status}").json()

    def decide(self, label, body):
        return self.post(f"ports/labels/{label_id(self.source.pk, label)}/decision/", body)

    def test_labels_merge_operations_and_port_list_without_raw_text_in_ids(self):
        body = self.labels()
        self.assertEqual(body["counts"], {"to_read": 3, "read": 0})
        first = body["items"][0]
        self.assertEqual((first["label"], first["operations"]), ("Port fictif A", 2))
        self.assertEqual(first["port_list_row"]["error_codes"], [])
        self.assertAlmostEqual(first["port_list_row"]["position"]["longitude"], 10.2)
        self.assertRegex(first["id"], r"^[0-9a-f]{32}$")
        ambiguous = next(item for item in body["items"] if item["label"] == "Port fictif B")
        self.assertIsNone(ambiguous["port_list_row"]["position"])
        self.assertTrue(ambiguous["port_list_row"]["error_codes"])

    def test_detail_shows_received_cells_and_where_the_name_appears(self):
        detail = self.get(f"ports/labels/{label_id(self.source.pk, 'Port fictif B')}/").json()
        self.assertEqual(detail["port_list_cells"]["headers"], ["nom", "latitude", "longitude"])
        self.assertEqual(detail["port_list_cells"]["cells"][0], "Port fictif B")
        self.assertEqual(detail["operation_lines"], [{"line": 4, "occurred_on": "2024-02-05"}])
        self.assertEqual(self.get("ports/labels/nope/").status_code, 404)

    def test_new_port_from_the_port_list(self):
        response = self.decide(
            "Port fictif A",
            {"interpretation": "port", "new_port": {"from_port_list": True}, "reason": "List"},
        )
        self.assertEqual(response.status_code, 200, response.content)
        reading = response.json()["reading"]
        self.assertEqual(reading["interpretation"], "port")
        self.assertEqual(reading["ports"][0]["location_source"], "sheet_row")
        self.assertEqual(self.labels()["counts"], {"to_read": 2, "read": 1})
        again = self.decide(
            "Port fictif A", {"interpretation": "not_a_port", "reason": "Second opinion"}
        )
        self.assertEqual((again.status_code, again.json()["code"]), (409, "conflict"))

    def test_ambiguous_position_must_be_entered_explicitly(self):
        response = self.decide(
            "Port fictif B",
            {"interpretation": "port", "new_port": {"from_port_list": True}, "reason": "List"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("new_port", response.json()["errors"])
        for position in ({"longitude": 0, "latitude": 0}, {"longitude": 200, "latitude": 39}):
            response = self.decide(
                "Port fictif B",
                {
                    "interpretation": "port",
                    "new_port": {"from_port_list": True, **position},
                    "reason": "Chart",
                },
            )
            self.assertEqual(response.status_code, 400, position)
        response = self.decide(
            "Port fictif B",
            {
                "interpretation": "port",
                "new_port": {
                    "from_port_list": True,
                    "longitude": -0.3098,
                    "latitude": 39.4387,
                    "country_code": "ES",
                },
                "reason": "West of Greenwich, checked on a chart",
            },
        )
        self.assertEqual(response.status_code, 200, response.content)
        port = Port.objects.get(name="Port fictif B")
        self.assertEqual((port.location_source, port.country_code), ("reviewer", "ES"))

    def test_several_ports_ship_and_not_a_port(self):
        first = Port.objects.create(name="Port un")
        second = Port.objects.create(name="Port deux")
        response = self.decide(
            "Port fictif A",
            {"interpretation": "ports", "ports": [str(first.pk)], "reason": "Pair"},
        )
        self.assertEqual(response.status_code, 400)
        response = self.decide(
            "Port fictif A",
            {"interpretation": "ports", "ports": [str(first.pk), str(second.pk)], "reason": "Pair"},
        )
        self.assertEqual(response.json()["reading"]["interpretation"], "ports")
        vessel = Vessel.objects.create(name="Navire fictif")
        response = self.decide(
            "Navire fictif",
            {"interpretation": "vessel", "vessel": str(vessel.pk), "reason": "Transfer"},
        )
        self.assertEqual(response.json()["reading"]["vessel"]["name"], "Navire fictif")
        response = self.decide(
            "Port fictif B", {"interpretation": "not_a_port", "reason": "A region"}
        )
        self.assertEqual(response.json()["reading"]["interpretation"], "not_a_port")
        self.assertEqual(
            sorted(PortAlias.objects.values_list("target", flat=True)),
            ["not_a_port", "ports", "vessel"],
        )
        read = self.labels("read")
        self.assertEqual(read["counts"], {"to_read": 0, "read": 3})

    def test_same_name_port_is_suggested_never_applied(self):
        port = Port.objects.create(name="port fictif a")
        item = self.labels()["items"][0]
        self.assertEqual(item["suggested_port"]["id"], str(port.pk))
        self.assertFalse(PortAlias.objects.exists())

    def test_reading_needs_the_review_permission_and_a_reason(self):
        outsider = Client()
        outsider.force_login(self.outsider)
        self.assertEqual(self.get("ports/labels/", client=outsider).status_code, 403)
        response = self.decide("Port fictif A", {"interpretation": "not_a_port", "reason": ""})
        self.assertEqual(response.status_code, 400)

    def test_port_list_row_at_zero_zero_is_not_a_usable_position(self):
        self.stage(ports_csv("Port fictif Zero,0,0"), sheet="Data_ports")
        item = next(i for i in self.labels()["items"] if i["label"] == "Port fictif Zero")
        self.assertIsNone(item["port_list_row"]["position"])
        response = self.decide(
            "Port fictif Zero",
            {"interpretation": "port", "new_port": {"from_port_list": True}, "reason": "List"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("new_port", response.json()["errors"])
        self.assertFalse(Port.objects.exists())

    def test_label_ids_are_keyed_not_plain_hashes(self):
        import hashlib

        plain = hashlib.sha256(f"{self.source.pk}\nPort fictif A".encode()).hexdigest()[:32]
        self.assertNotEqual(label_id(self.source.pk, "Port fictif A"), plain)

    def test_port_search_and_vessels(self):
        Port.objects.create(name="Port fictif Nord")
        Port.objects.create(name="Autre")
        names = [item["name"] for item in self.get("ports/?q=fictif").json()["items"]]
        self.assertEqual(names, ["Port fictif Nord"])
        self.assertEqual(self.get("vessels/").json(), {"items": []})
