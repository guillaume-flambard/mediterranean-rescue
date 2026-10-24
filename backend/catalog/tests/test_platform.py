import json
from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, TransactionTestCase, override_settings

from catalog.imports import apply_batch, stage_payload
from catalog.models import Event, ImportBatch, PublicationAudit, Source, StagedRecord
from catalog.schema import schema
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

    def test_drafts_and_unapproved_sources_never_reach_graph(self):
        event = self.event()
        result = schema.execute_sync("{ events { totalCount items { id source { name } } } }")
        self.assertIsNone(result.errors)
        self.assertEqual(result.data["events"]["totalCount"], 0)
        self.assertIsNone(
            schema.execute_sync(
                "query($id: UUID!){event(id:$id){id}}", variable_values={"id": str(event.id)}
            ).data["event"]
        )
        self.publish(event)
        self.source.rights_approved = False
        self.source.save()
        self.assertEqual(
            schema.execute_sync("{events{totalCount}}").data["events"]["totalCount"], 0
        )

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
        result = schema.execute_sync(
            "{events{totalCount items{id kind people position{longitude latitude precision} source{name}}}}"
        )
        self.assertIsNone(result.errors)
        self.assertEqual(result.data["events"]["totalCount"], 1)
        self.assertIsNone(result.data["events"]["items"][0]["people"])
        self.assertEqual(result.data["events"]["items"][0]["kind"], "RESCUE")
        set_publication(
            event_id=event.pk, actor=self.actor, publish=False, reason="Correction requested"
        )
        self.assertEqual(Event.objects.public().count(), 0)
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
        q = "query($f:EventFilter){events(filters:$f){totalCount} mapPoints(filters:$f){locatedCount points{id}}}"
        filters = {
            "start": "2024-02-29",
            "end": "2024-02-29",
            "bounds": {"west": 11, "south": 33, "east": 13, "north": 35},
        }
        result = schema.execute_sync(q, variable_values={"f": filters})
        self.assertIsNone(result.errors)
        self.assertEqual(result.data["events"]["totalCount"], 1)
        self.assertEqual(result.data["mapPoints"]["locatedCount"], 1)
        filters["bounds"]["west"] = 14
        self.assertTrue(schema.execute_sync(q, variable_values={"f": filters}).errors)
        self.assertTrue(
            schema.execute_sync(
                '{events(filters:{start:"2025-01-01",end:"2024-01-01"}){totalCount}}'
            ).errors
        )

    def test_graphql_contract_rejects_unsafe_fields_and_limits(self):
        self.assertTrue(schema.execute_sync("{events{items{externalId}}}").errors)
        self.assertTrue(schema.execute_sync("{events(limit:101){totalCount}}").errors)
        aliases = " ".join(f"a{i}:dataMode" for i in range(11))
        self.assertTrue(schema.execute_sync("{" + aliases + "}").errors)
        self.assertTrue(schema.execute_sync('mutation { publishEvent(id:"x") {id} }').errors)

    def test_query_budget_is_bounded_for_relations(self):
        for i in range(5):
            self.publish(self.event(external_id=str(i)))
        with self.assertNumQueries(3):
            result = schema.execute_sync(
                "{events{totalCount items{id source{name} evidence{url} vessel{name} voyage{title} port{name}}}}"
            )
        self.assertIsNone(result.errors)

    def test_training_data_does_not_leak_into_production(self):
        self.source.synthetic = True
        self.source.save()
        self.publish(self.event())
        self.assertEqual(Event.objects.public().count(), 0)
        with override_settings(DATA_MODE="training"):
            self.assertEqual(Event.objects.public().count(), 1)

    def test_http_csrf_size_and_health(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            "/graphql/", data=json.dumps({"query": "{dataMode}"}), content_type="application/json"
        )
        self.assertEqual(response.status_code, 403)
        token = client.get("/api/csrf/").json()["csrfToken"]
        response = client.post(
            "/graphql/",
            data=json.dumps({"query": "{dataMode}"}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["dataMode"], "production")
        self.assertEqual(client.get("/api/health/").status_code, 200)
        response = client.post(
            "/graphql/", data="x" * 65537, content_type="application/json", HTTP_X_CSRFTOKEN=token
        )
        self.assertEqual(response.status_code, 413)

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

    def test_browser_query_without_content_length_and_dev_proxy_origin(self):
        client = Client(enforce_csrf_checks=True)
        response = client.get("/graphql/", {"query": "{dataMode}"}, CONTENT_LENGTH="")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["dataMode"], "production")
        token = client.get("/api/csrf/").json()["csrfToken"]
        with override_settings(CSRF_TRUSTED_ORIGINS=["http://127.0.0.1:5173"]):
            response = client.post(
                "/graphql/",
                data=json.dumps({"query": "{dataMode}"}),
                content_type="application/json",
                HTTP_X_CSRFTOKEN=token,
                HTTP_ORIGIN="http://127.0.0.1:5173",
            )
            self.assertEqual(response.status_code, 200)

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
