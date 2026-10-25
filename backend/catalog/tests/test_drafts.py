"""Event drafts from approved identities (ADR 0006). Synthetic inputs, real PostGIS."""

from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.test import Client, override_settings

from catalog.admin import EventAdmin
from catalog.crosswalk import approve_link, approve_port_alias, classify_port_label
from catalog.drafts import create_drafts, plan_drafts
from catalog.models import Event, Port, PublicationAudit, SourceIdentity
from catalog.services import set_publication
from catalog.tests.test_crosswalk import CrosswalkTestCase, ports_csv
from catalog.tests.test_sheets import OTHER_HEADER, ops_csv, ops_row

# Other_data row with deaths in column 8; every other optional cell empty.
OTHER_HEADER_ROW = "02/04/2024,Dead & Missing,33° 55,13° 55,,,,{deaths},,,,,,,"


def outcomes(plan):
    return [item.outcome for item in plan]


class DraftTestCase(CrosswalkTestCase):
    def setUp(self):
        super().setUp()
        self.reviewer.user_permissions.add(Permission.objects.get(codename="add_event"))
        self.reviewer = get_user_model().objects.get(pk=self.reviewer.pk)

    def staged_and_linked(self, content, sheet="Data_operations"):
        snapshot, _ = self.stage(content, sheet=sheet)
        for row in snapshot.rows.order_by("line"):
            if not row.error_codes:
                approve_link(row=row, actor=self.reviewer, reason="Reviewed")
        return snapshot


class DraftCreationTests(DraftTestCase):
    def test_ready_rows_become_private_drafts_with_translated_fields(self):
        snapshot = self.staged_and_linked(
            ops_csv(
                ops_row(nb_survivor="42", female="12", under_18="8", male="n/a"),
                ops_row(date="04/02/2024", type_ops="Transfer", latitude="", longitude=""),
            )
        )
        self.assertEqual(outcomes(plan_drafts(snapshot)), ["ready", "ready"])
        result = create_drafts(snapshot=snapshot, actor=self.reviewer, reason="First drafts")
        self.assertEqual((len(result.created), result.skipped), (2, []))
        rescue = Event.objects.get(kind="rescue")
        identity = snapshot.rows.get(line=2).identity_link.identity
        self.assertEqual(rescue.external_id, identity.external_id)
        self.assertEqual((rescue.source, rescue.source_url), (self.source, self.source.url))
        self.assertEqual(str(rescue.occurred_on), "2024-02-03")
        self.assertEqual(rescue.title, "Rescue on 2024-02-03")
        self.assertEqual((rescue.people, rescue.women, rescue.minors), (42, 12, 8))
        self.assertEqual(rescue.status, "draft")
        self.assertIsNone(rescue.published_at)
        self.assertEqual(rescue.location_precision, "reported")
        self.assertAlmostEqual(rescue.location.x, 12.25)
        self.assertAlmostEqual(rescue.location.y, 34.5)
        transfer = Event.objects.get(kind="transfer")
        self.assertIsNone(transfer.people)
        self.assertIsNone(transfer.location)
        self.assertEqual(transfer.location_precision, "unknown")
        identity.refresh_from_db()
        self.assertEqual(identity.event, rescue)
        self.assertEqual(identity.drafted_from, snapshot.rows.get(line=2))
        self.assertEqual(
            (identity.drafted_by, identity.draft_reason), (self.reviewer, "First drafts")
        )
        self.assertEqual(PublicationAudit.objects.count(), 0)

    @override_settings(DATA_MODE="training")
    def test_drafts_never_reach_the_public_api(self):
        # Rights approved, so only the draft status can keep the event private.
        self.source.rights_approved = True
        self.source.license_note = "Synthetic fixture approved for tests"
        self.source.save()
        snapshot = self.staged_and_linked(ops_csv(ops_row()))
        create_drafts(snapshot=snapshot, actor=self.reviewer, reason="Drafts")
        response = Client().get("/api/v1/events/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_count"], 0)

    def test_replay_and_corrections_never_overwrite(self):
        first = self.staged_and_linked(ops_csv(ops_row(nb_survivor="40")))
        create_drafts(snapshot=first, actor=self.reviewer, reason="Drafts")
        self.assertEqual(outcomes(plan_drafts(first)), ["already_drafted"])
        again = create_drafts(snapshot=first, actor=self.reviewer, reason="Again")
        self.assertEqual(
            (again.created, [s.outcome for s in again.skipped]), ([], ["already_drafted"])
        )
        corrected, _ = self.stage(ops_csv(ops_row(nb_survivor="42")))
        approve_link(
            row=corrected.rows.get(),
            actor=self.reviewer,
            reason="Same rescue, corrected",
            identity=first.rows.get().identity_link.identity,
        )
        self.assertEqual(outcomes(plan_drafts(corrected)), ["revision_needed"])
        create_drafts(snapshot=corrected, actor=self.reviewer, reason="Drafts")
        self.assertEqual(Event.objects.get().people, 40)

    def test_unchanged_content_in_a_new_export_is_already_drafted(self):
        first = self.staged_and_linked(ops_csv(ops_row()))
        create_drafts(snapshot=first, actor=self.reviewer, reason="Drafts")
        second, _ = self.stage(ops_csv(ops_row(date="05/02/2024"), ops_row()))
        approve_link(
            row=second.rows.get(line=3),
            actor=self.reviewer,
            reason="Unchanged",
            identity=first.rows.get().identity_link.identity,
        )
        self.assertEqual(outcomes(plan_drafts(second)), ["not_linked", "already_drafted"])


class DraftSafetyTests(DraftTestCase):
    def test_inconsistent_counts_are_listed_not_truncated(self):
        snapshot = self.staged_and_linked(
            ops_csv(ops_row(nb_survivor="3", female="5"), ops_row(date="04/02/2024"))
        )
        result = create_drafts(snapshot=snapshot, actor=self.reviewer, reason="Drafts")
        self.assertEqual(len(result.created), 1)
        self.assertEqual(
            [(s.line, s.outcome) for s in result.skipped], [(2, "inconsistent_counts")]
        )
        self.assertFalse(Event.objects.filter(occurred_on="2024-02-03").exists())

    def test_deaths_never_become_people(self):
        content = (OTHER_HEADER + "\n" + OTHER_HEADER_ROW.format(deaths="7") + "\n").encode()
        snapshot = self.staged_and_linked(content, sheet="Other_data")
        create_drafts(snapshot=snapshot, actor=self.reviewer, reason="Drafts")
        event = Event.objects.get()
        self.assertEqual(event.kind, "dead_missing")
        self.assertIsNone(event.people)

    def test_port_only_from_a_single_port_reading(self):
        port = Port.objects.create(name="Port fictif")
        approve_port_alias(
            source=self.source, label="Port fictif", actor=self.reviewer, reason="r", ports=[port]
        )
        other = Port.objects.create(name="Autre port")
        approve_port_alias(
            source=self.source,
            label="Port fictif & Autre port",
            actor=self.reviewer,
            reason="r",
            ports=[port, other],
        )
        classify_port_label(
            source=self.source, label="Région fictive", actor=self.reviewer, reason="r"
        )
        snapshot = self.staged_and_linked(
            ops_csv(
                ops_row(date="01/02/2024", Port_disembarkation="Port fictif"),
                ops_row(date="02/02/2024", Port_disembarkation="Port fictif & Autre port"),
                ops_row(date="03/02/2024", Port_disembarkation="Région fictive"),
                ops_row(date="04/02/2024", Port_disembarkation="Port inconnu"),
            )
        )
        create_drafts(snapshot=snapshot, actor=self.reviewer, reason="Drafts")
        ports = {str(e.occurred_on): e.port for e in Event.objects.all()}
        self.assertEqual(
            ports,
            {"2024-02-01": port, "2024-02-02": None, "2024-02-03": None, "2024-02-04": None},
        )

    def test_guards(self):
        snapshot = self.staged_and_linked(ops_csv(ops_row(), ops_row(date="04/02/2024")))
        snapshot.rows.get(line=3).identity_link.delete()
        self.assertEqual(outcomes(plan_drafts(snapshot)), ["ready", "not_linked"])
        with self.assertRaises(PermissionDenied):
            create_drafts(snapshot=snapshot, actor=self.outsider, reason="x")
        with self.assertRaises(ValidationError):
            create_drafts(snapshot=snapshot, actor=self.reviewer, reason=" ")
        ports, _ = self.stage(ports_csv("Port fictif A,36° 48.0,10° 12.0"), sheet="Data_ports")
        self.assertEqual(outcomes(plan_drafts(ports)), ["not_an_event_sheet"])
        self.assertEqual(Event.objects.count(), 0)

    def test_publication_still_needs_source_rights(self):
        snapshot = self.staged_and_linked(ops_csv(ops_row()))
        create_drafts(snapshot=snapshot, actor=self.reviewer, reason="Drafts")
        editor = get_user_model().objects.create_superuser(username="editor", password=None)
        with self.assertRaises(ValidationError):
            set_publication(
                event_id=Event.objects.get().pk, actor=editor, publish=True, reason="Too early"
            )
        self.assertEqual(Event.objects.get().status, "draft")


class DraftReviewFindingTests(DraftTestCase):
    """Regressions for the independent review of the drafts slice."""

    def test_zero_zero_position_is_never_drafted(self):
        snapshot = self.staged_and_linked(ops_csv(ops_row(latitude="0", longitude="0")))
        self.assertEqual(outcomes(plan_drafts(snapshot)), ["position_to_review"])
        create_drafts(snapshot=snapshot, actor=self.reviewer, reason="Drafts")
        self.assertEqual(Event.objects.count(), 0)

    def test_older_export_is_stale(self):
        older = self.staged_and_linked(ops_csv(ops_row()))
        self.staged_and_linked(ops_csv(ops_row(date="04/02/2024")))
        self.assertEqual(outcomes(plan_drafts(older)), ["stale_snapshot"])
        create_drafts(snapshot=older, actor=self.reviewer, reason="Drafts")
        self.assertEqual(Event.objects.count(), 0)

    def test_a_row_never_produces_two_drafts(self):
        snapshot = self.staged_and_linked(ops_csv(ops_row()))
        create_drafts(snapshot=snapshot, actor=self.reviewer, reason="Drafts")
        row = snapshot.rows.get()
        row.identity_link.delete()
        approve_link(row=row, actor=self.reviewer, reason="Relinked by mistake")
        self.assertEqual(outcomes(plan_drafts(snapshot)), ["row_already_drafted"])

    def test_invalid_draft_names_the_problem_without_values(self):
        snapshot = self.staged_and_linked(ops_csv(ops_row()))
        identity = snapshot.rows.get().identity_link.identity
        Event.objects.create(
            source=self.source,
            external_id=identity.external_id,
            kind="rescue",
            occurred_on="2024-01-01",
            title="Collision",
            source_url="https://example.org/x",
        )
        (plan,) = plan_drafts(snapshot)
        self.assertEqual(plan.outcome, "invalid_draft")
        self.assertTrue(plan.detail)
        self.assertNotIn("2024", plan.detail)

    def test_database_refuses_a_half_traced_identity(self):
        snapshot = self.staged_and_linked(ops_csv(ops_row()))
        identity = snapshot.rows.get().identity_link.identity
        event = Event.objects.create(
            source=self.source,
            external_id="manual-1",
            kind="rescue",
            occurred_on="2024-01-01",
            title="Manual",
            source_url="https://example.org/x",
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            SourceIdentity.objects.filter(pk=identity.pk).update(event=event)

    def test_created_events_are_reported_with_their_line_and_locked_in_admin(self):
        snapshot = self.staged_and_linked(ops_csv(ops_row()))
        result = create_drafts(snapshot=snapshot, actor=self.reviewer, reason="Drafts")
        ((line, event_id),) = result.created
        self.assertEqual(line, 2)
        readonly = EventAdmin(Event, site).get_readonly_fields(None, Event.objects.get(pk=event_id))
        self.assertIn("source", readonly)
        self.assertIn("external_id", readonly)
