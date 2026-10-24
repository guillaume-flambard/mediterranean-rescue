import json
from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, TransactionTestCase, override_settings

from catalog.imports import apply_batch, stage_payload
from catalog.models import Event, ImportBatch, Port, PublicationAudit, Source, StagedRecord
from catalog.services import set_publication


@override_settings(
    DATA_MODE="production",
    SECURE_SSL_REDIRECT=False,
    SESSION_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False,
)
class PlatformTests(TestCase):
    def setUp(self):
        self.source = Source.objects.create(
            key="test",
            name="Independent test source",
            url="https://example.org",
            license_note="Synthetic fixture approved for tests",
            rights_approved=True,
        )
        self.actor = get_user_model().objects.create_superuser(username="reviewer", password=None)
        self.row = {
            "external_id": "evt-1",
            "kind": "rescue",
            "occurred_on": "2024-02-29",
            "title": "Test fixture",
            "source_url": "https://example.org/event",
            "people": None,
            "longitude": 12.0,
            "latitude": 34.0,
            "location_precision": "approximate",
        }

    def event(self, **changes):
        values = {
            "source": self.source,
            "external_id": "direct",
            "kind": "rescue",
            "occurred_on": date(2024, 2, 29),
            "title": "Fixture",
            "source_url": "https://example.org/event",
            "location": Point(12, 34, srid=4326),
            "location_precision": "approximate",
        }
        values.update(changes)
        return Event.objects.create(**values)

    def publish(self, event):
        return set_publication(
            event_id=event.pk, actor=self.actor, publish=True, reason="Fixture review"
        )

    def test_drafts_and_unapproved_sources_never_reach_api(self):
        event = self.event()
        self.assertEqual(self.client.get("/api/v1/events/").json()["total_count"], 0)
        self.assertEqual(self.client.get(f"/api/v1/events/{event.id}/").status_code, 404)
        self.assertEqual(self.client.get(f"/api/v1/events/{event.id}/evidence/").status_code, 404)
        self.publish(event)
        self.source.rights_approved = False
        self.source.save()
        self.assertEqual(self.client.get("/api/v1/events/").json()["total_count"], 0)
        self.assertEqual(self.client.get("/api/v1/map-points/").json()["located_count"], 0)
        self.assertEqual(self.client.get(f"/api/v1/events/{event.id}/").status_code, 404)

    def test_publication_requires_permission_rights_and_reason(self):
        event = self.event()
        user = get_user_model().objects.create_user(username="editor", is_staff=True)
        with self.assertRaises(PermissionDenied):
            set_publication(event_id=event.pk, actor=user, publish=True, reason="No permission")
        self.source.rights_approved = False
        self.source.save()
        with self.assertRaises(ValidationError):
            self.publish(event)
        self.source.rights_approved = True
        self.source.save()
        with self.assertRaises(ValidationError):
            set_publication(event_id=event.pk, actor=self.actor, publish=True, reason="")
        self.assertEqual(PublicationAudit.objects.count(), 0)

    def test_publication_audit_and_withdrawal(self):
        event = self.publish(self.event())
        response = self.client.get("/api/v1/events/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_count"], 1)
        self.assertIsNone(data["items"][0]["people"])
        self.assertEqual(data["items"][0]["kind"], "rescue")
        detail = self.client.get(f"/api/v1/events/{event.id}/").json()
        self.assertEqual(detail["position"]["longitude"], 12)
        self.assertNotIn("external_id", detail)
        self.assertNotIn("rights_approved", detail["source"])
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        set_publication(
            event_id=event.pk, actor=self.actor, publish=False, reason="Correction requested"
        )
        self.assertEqual(self.client.get(f"/api/v1/events/{event.id}/").status_code, 404)
        self.assertEqual(PublicationAudit.objects.count(), 2)

    def test_database_rejects_unreviewed_publication(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.event(status="published")

    def test_import_idempotence_unknowns_and_no_implicit_publication(self):
        payload = json.dumps([self.row]).encode()
        batch, created = stage_payload(source=self.source, content=payload)
        self.assertTrue(created)
        duplicate, created = stage_payload(source=self.source, content=payload)
        self.assertFalse(created)
        self.assertEqual(batch.pk, duplicate.pk)
        self.assertEqual(apply_batch(batch_id=batch.pk), 1)
        self.assertEqual(apply_batch(batch_id=batch.pk), 0)
        event = Event.objects.get(external_id="evt-1")
        self.assertIsNone(event.people)
        self.assertEqual(event.status, "draft")
        self.assertEqual(StagedRecord.objects.count(), 1)

    def test_invalid_import_is_atomic_and_duplicate_identity_refused(self):
        for invalid in [
            {**self.row, "people": True},
            {**self.row, "occurred_on": "2023-02-29"},
            {**self.row, "longitude": None},
            {**self.row, "source_url": "javascript:alert(1)"},
        ]:
            with self.assertRaises(ValidationError):
                stage_payload(source=self.source, content=json.dumps([self.row, invalid]).encode())
        with self.assertRaises(ValidationError):
            stage_payload(source=self.source, content=json.dumps([self.row, self.row]).encode())
        self.assertEqual(ImportBatch.objects.count(), 0)
        self.assertEqual(Event.objects.count(), 0)

    def test_existing_record_cannot_be_silently_overwritten(self):
        self.event(external_id="evt-1")
        rows = [{**self.row, "external_id": "new"}, self.row]
        batch, _ = stage_payload(source=self.source, content=json.dumps(rows).encode())
        with self.assertRaises(ValidationError):
            apply_batch(batch_id=batch.pk)
        self.assertFalse(Event.objects.filter(external_id="new").exists())
        batch.refresh_from_db()
        self.assertEqual(batch.status, "staged")

    def test_bounds_and_dates_use_same_public_queryset(self):
        self.publish(self.event())
        filters = {
            "start": "2024-02-29",
            "end": "2024-02-29",
            "bbox": "11,33,13,35",
            "kind": "rescue",
        }
        self.assertEqual(self.client.get("/api/v1/events/", filters).json()["total_count"], 1)
        self.assertEqual(self.client.get("/api/v1/map-points/", filters).json()["located_count"], 1)
        for invalid in [
            {"bbox": "14,33,13,35"},
            {"start": "2025-01-01", "end": "2024-01-01"},
            {"start": "2023-02-29"},
            {"bbox": "nan,0,1,1"},
            {"kind": "unknown"},
            {"bbox": "1,2"},
            {"unknown": "x"},
        ]:
            for path in ["/api/v1/events/", "/api/v1/map-points/"]:
                self.assertEqual(self.client.get(path, invalid).status_code, 400)
        filters["bbox"] = "0,0,1,1"
        self.assertEqual(self.client.get("/api/v1/events/", filters).json()["total_count"], 0)

    def test_words_search_title_summary_and_port(self):
        port = Port.objects.create(name="Port fictif")
        self.publish(self.event(external_id="a", title="Rescue near the coast", port=port))
        self.publish(self.event(external_id="b", title="Other", summary="Fictional transfer"))

        def titles(q):
            items = self.client.get("/api/v1/events/", {"q": q}).json()["items"]
            return sorted(item["title"] for item in items)

        self.assertEqual(titles("fictif"), ["Rescue near the coast"])
        self.assertEqual(titles("FICTIONAL"), ["Other"])
        self.assertEqual(titles("rescue coast"), ["Rescue near the coast"])
        self.assertEqual(
            self.client.get("/api/v1/map-points/", {"q": "nowhere"}).json()["located_count"], 0
        )

    def test_rest_contract_rejects_writes_and_invalid_pagination(self):
        for values in [{"limit": 101}, {"limit": 0}, {"offset": -1}, {"offset": 100001}]:
            self.assertEqual(self.client.get("/api/v1/events/", values).status_code, 400)
        self.assertEqual(
            self.client.get("/api/v1/events/?kind=rescue&kind=transfer").status_code, 400
        )
        for method in ["post", "put", "patch", "delete"]:
            self.assertEqual(getattr(self.client, method)("/api/v1/events/").status_code, 405)
        self.assertEqual(self.client.get("/graphql/").status_code, 404)

    def test_query_budget_is_bounded_for_relations(self):
        for i in range(5):
            self.publish(self.event(external_id=str(i)))
        with self.assertNumQueries(2):
            response = self.client.get("/api/v1/events/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["items"]), 5)
        page = self.client.get("/api/v1/events/", {"limit": 2}).json()
        self.assertTrue(page["has_next"])
        self.assertEqual(len(page["items"]), 2)

    def test_map_cap_and_http_training_isolation(self):
        from django.utils import timezone

        Event.objects.bulk_create(
            [
                Event(
                    source=self.source,
                    external_id=f"cap-{i}",
                    kind="rescue",
                    occurred_on=date(2024, 2, 29),
                    title="Synthetic test fixture",
                    source_url="https://example.org",
                    location=Point(12, 34, srid=4326),
                    location_precision="approximate",
                    status="published",
                    published_at=timezone.now(),
                    reviewed_by=self.actor,
                )
                for i in range(2001)
            ]
        )
        result = self.client.get("/api/v1/map-points/").json()
        self.assertEqual(len(result["points"]), 2000)
        self.assertEqual(result["located_count"], 2001)
        self.assertTrue(result["truncated"])
        with override_settings(DATA_MODE="training"):
            self.assertEqual(self.client.get("/api/v1/events/").json()["total_count"], 0)
            self.assertEqual(self.client.get("/api/v1/map-points/").json()["located_count"], 0)

    def test_training_data_does_not_leak_into_production(self):
        self.source.synthetic = True
        self.source.save()
        self.publish(self.event())
        self.assertEqual(Event.objects.public().count(), 0)
        with override_settings(DATA_MODE="training"):
            self.assertEqual(Event.objects.public().count(), 1)

    def test_http_csrf_size_and_health(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.get("/api/v1/events/").status_code, 200)
        self.assertEqual(client.post("/admin/login/", {"username": "invalid"}).status_code, 403)
        self.assertIn("csrfToken", client.get("/api/csrf/").json())
        self.assertEqual(client.get("/api/health/").status_code, 200)
        self.assertEqual(
            client.post(
                "/api/v1/events/", data="x" * 65537, content_type="application/json"
            ).status_code,
            413,
        )

    def test_published_relations_cannot_be_changed_indirectly_in_admin(self):
        from django.contrib import admin
        from django.test import RequestFactory

        from catalog.admin import EvidenceForm
        from catalog.models import Evidence, Port, Vessel, Voyage

        vessel = Vessel.objects.create(name="Fixture vessel")
        port = Port.objects.create(name="Fixture port")
        voyage = Voyage.objects.create(
            vessel=vessel, title="Fixture voyage", started_on=date(2024, 1, 1)
        )
        event = self.publish(self.event(vessel=vessel, port=port, voyage=voyage))
        evidence = Evidence.objects.create(
            event=event, label="Fixture evidence", url="https://example.org"
        )
        request = RequestFactory().get("/admin/")
        request.user = self.actor
        for model, obj in [
            (Event, event),
            (Vessel, vessel),
            (Port, port),
            (Voyage, voyage),
            (Evidence, evidence),
        ]:
            self.assertFalse(admin.site._registry[model].has_change_permission(request, obj))
            self.assertFalse(admin.site._registry[model].has_delete_permission(request, None))
        source_admin = admin.site._registry[Source]
        fields = source_admin.get_readonly_fields(request, self.source)
        for name in ["url", "name", "license_note", "synthetic"]:
            self.assertIn(name, fields)
        form = EvidenceForm(
            data={"event": str(event.pk), "label": "Injection", "url": "https://example.org/new"}
        )
        self.assertFalse(form.is_valid())

    def test_blank_license_is_never_public(self):
        self.publish(self.event())
        self.source.license_note = "   "
        self.source.save()
        self.assertEqual(Event.objects.public().count(), 0)

    def test_browser_query_without_content_length_and_paginated_evidence(self):
        from catalog.models import Evidence

        response = self.client.get("/api/v1/events/", CONTENT_LENGTH="")
        self.assertEqual(response.status_code, 200)
        event = self.publish(self.event(location=None, location_precision="unknown"))
        for i in range(3):
            Evidence.objects.create(event=event, label=str(i), url="https://example.org")
        result = self.client.get(f"/api/v1/events/{event.id}/evidence/", {"limit": 2}).json()
        self.assertEqual(len(result["items"]), 2)
        self.assertTrue(result["has_next"])
        self.assertEqual(result["total_count"], 3)
        self.assertIsNone(self.client.get(f"/api/v1/events/{event.id}/").json()["position"])
        self.assertEqual(self.client.get("/api/v1/map-points/").json()["located_count"], 0)

    def test_stale_admin_forms_cannot_undo_publication_or_rights_revocation(self):
        from types import SimpleNamespace

        from django.contrib import admin
        from django.test import RequestFactory

        request = RequestFactory().post("/admin/")
        request.user = self.actor
        event = self.event()
        stale_event = Event.objects.get(pk=event.pk)
        self.publish(event)
        stale_event.title = "A stale edit"
        with self.assertRaises(PermissionDenied):
            admin.site._registry[Event].save_model(
                request, stale_event, SimpleNamespace(changed_data=["title"]), True
            )
        event.refresh_from_db()
        self.assertEqual(event.status, "published")
        self.assertEqual(event.title, "Fixture")
        stale_source = Source.objects.get(pk=self.source.pk)
        self.source.rights_approved = False
        self.source.save()
        with self.assertRaises(PermissionDenied):
            admin.site._registry[Source].save_model(
                request, stale_source, SimpleNamespace(changed_data=["name"]), True
            )
        self.source.refresh_from_db()
        self.assertFalse(self.source.rights_approved)

    def test_evidence_cannot_be_moved_out_of_a_published_event(self):
        from types import SimpleNamespace

        from django.contrib import admin
        from django.test import RequestFactory

        from catalog.models import Evidence

        first = self.event()
        second = self.event(external_id="second")
        evidence = Evidence.objects.create(event=first, label="Fixture", url="https://example.org")
        stale = Evidence.objects.get(pk=evidence.pk)
        self.publish(first)
        stale.event = second
        request = RequestFactory().post("/admin/")
        request.user = self.actor
        with self.assertRaises(PermissionDenied):
            admin.site._registry[Evidence].save_model(
                request, stale, SimpleNamespace(changed_data=["event"]), True
            )
        evidence.refresh_from_db()
        self.assertEqual(evidence.event_id, first.pk)


class MigrationContractTests(TransactionTestCase):
    def test_initial_catalog_migration_is_reversible_on_isolated_test_database(self):
        from django.db import connection
        from django.db.migrations.executor import MigrationExecutor

        self.assertTrue(connection.settings_dict["NAME"].startswith("test_"))
        executor = MigrationExecutor(connection)
        try:
            executor.migrate([("catalog", None)])
            self.assertNotIn("catalog_event", connection.introspection.table_names())
        finally:
            MigrationExecutor(connection).migrate([("catalog", "0001_initial")])
        self.assertIn("catalog_event", connection.introspection.table_names())
