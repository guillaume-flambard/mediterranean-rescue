"""Reviewed revisions of existing drafts (ADR 0007). Synthetic inputs, real PostGIS."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError

from catalog.crosswalk import approve_link, approve_port_alias
from catalog.drafts import create_drafts, plan_drafts
from catalog.models import Event, EventRevision, Port, PublicationAudit
from catalog.revisions import apply_revision, propose_revision, reject_revision
from catalog.tests.test_drafts import DraftTestCase, outcomes
from catalog.tests.test_sheets import ops_csv, ops_row


class RevisionTestCase(DraftTestCase):
    def setUp(self):
        super().setUp()
        self.reviewer.user_permissions.add(Permission.objects.get(codename="change_event"))
        self.reviewer = get_user_model().objects.get(pk=self.reviewer.pk)

    def drafted(self, **values):
        snapshot = self.staged_and_linked(ops_csv(ops_row(**values)))
        create_drafts(snapshot=snapshot, actor=self.reviewer, reason="Drafts")
        row = snapshot.rows.get()
        return row.identity_link.identity, Event.objects.get(
            external_id=row.identity_link.identity.external_id
        )

    def corrected(self, identity, **values):
        snapshot, _ = self.stage(ops_csv(ops_row(**values)))
        row = snapshot.rows.get()
        approve_link(row=row, actor=self.reviewer, reason="Same rescue", identity=identity)
        return row


class ApplyTests(RevisionTestCase):
    def test_exact_changes_are_proposed_and_applied_without_publication(self):
        identity, event = self.drafted(nb_survivor="40", latitude="34.5")
        row = self.corrected(identity, nb_survivor="42", latitude="34.6")
        self.assertEqual(outcomes(plan_drafts(row.snapshot)), ["revision_needed"])
        proposal = propose_revision(row)
        self.assertEqual(sorted(proposal.changes), ["location", "people"])
        self.assertEqual(proposal.changes["people"], (40, 42))
        self.assertEqual(proposal.conflicts, ())
        revision = apply_revision(row=row, actor=self.reviewer, reason="Count corrected in export")
        event.refresh_from_db()
        identity.refresh_from_db()
        self.assertEqual(event.people, 42)
        self.assertAlmostEqual(event.location.y, 34.6)
        self.assertEqual(event.status, "draft")
        self.assertEqual(identity.drafted_from, row)
        self.assertEqual(
            (revision.decision, revision.from_row, revision.to_row),
            ("applied", identity.links.order_by("created_at").first().row, row),
        )
        self.assertEqual(revision.changes["people"], [40, 42])
        self.assertEqual(outcomes(plan_drafts(row.snapshot)), ["already_drafted"])
        self.assertEqual(PublicationAudit.objects.count(), 0)

    def test_manual_edit_on_a_changed_field_is_a_conflict(self):
        identity, event = self.drafted(nb_survivor="40")
        Event.objects.filter(pk=event.pk).update(people=41, summary="Edited by hand")
        row = self.corrected(identity, nb_survivor="42")
        self.assertEqual(propose_revision(row).conflicts, ("people",))
        with self.assertRaises(ValidationError):
            apply_revision(row=row, actor=self.reviewer, reason="r")
        event.refresh_from_db()
        self.assertEqual(event.people, 41)
        self.assertFalse(EventRevision.objects.exists())

    def test_manual_edit_elsewhere_is_kept(self):
        identity, event = self.drafted(nb_survivor="40")
        Event.objects.filter(pk=event.pk).update(summary="Edited by hand", title="Edited title")
        row = self.corrected(identity, nb_survivor="42")
        apply_revision(row=row, actor=self.reviewer, reason="r")
        event.refresh_from_db()
        self.assertEqual(
            (event.people, event.summary, event.title), (42, "Edited by hand", "Edited title")
        )

    def test_published_event_is_refused_and_withdrawn_stays_withdrawn(self):
        identity, event = self.drafted(nb_survivor="40")
        Event.objects.filter(pk=event.pk).update(
            status="published", published_at="2026-10-24T12:00Z", reviewed_by=self.reviewer
        )
        row = self.corrected(identity, nb_survivor="42")
        self.assertEqual(propose_revision(row).blocked_by, "event_published")
        with self.assertRaises(ValidationError):
            apply_revision(row=row, actor=self.reviewer, reason="r")
        Event.objects.filter(pk=event.pk).update(status="withdrawn")
        apply_revision(row=row, actor=self.reviewer, reason="Corrected while withdrawn")
        event.refresh_from_db()
        self.assertEqual((event.status, event.people), ("withdrawn", 42))


class RejectTests(RevisionTestCase):
    def test_rejection_is_kept_for_the_same_content_only(self):
        identity, event = self.drafted(nb_survivor="40")
        row = self.corrected(identity, nb_survivor="42")
        revision = reject_revision(row=row, actor=self.reviewer, reason="Export typo")
        self.assertEqual(revision.decision, "rejected")
        event.refresh_from_db()
        self.assertEqual(event.people, 40)
        self.assertEqual(outcomes(plan_drafts(row.snapshot)), ["revision_rejected"])
        # Different bytes (padded cell), same normalized content.
        again = self.corrected(identity, nb_survivor=" 42")
        self.assertEqual(outcomes(plan_drafts(again.snapshot)), ["revision_rejected"])
        self.assertEqual(propose_revision(again).blocked_by, "revision_rejected")
        with self.assertRaises(ValidationError):
            apply_revision(row=again, actor=self.reviewer, reason="Applied by mistake")
        different = self.corrected(identity, nb_survivor="43")
        self.assertEqual(outcomes(plan_drafts(different.snapshot)), ["revision_needed"])


class GuardTests(RevisionTestCase):
    def test_inconsistent_counts_are_refused(self):
        identity, event = self.drafted(nb_survivor="40", female="10")
        row = self.corrected(identity, nb_survivor="5", female="10")
        self.assertEqual(propose_revision(row).blocked_by, "inconsistent_counts")
        with self.assertRaises(ValidationError):
            apply_revision(row=row, actor=self.reviewer, reason="r")

    def test_only_rows_needing_a_revision_on_the_latest_export(self):
        identity, event = self.drafted(nb_survivor="40")
        first_row = identity.drafted_from
        with self.assertRaises(ValidationError):
            apply_revision(row=first_row, actor=self.reviewer, reason="Nothing to revise")
        older = self.corrected(identity, nb_survivor="42")
        self.corrected(identity, nb_survivor="44")
        self.assertEqual(propose_revision(older).blocked_by, "stale_snapshot")
        with self.assertRaises(ValidationError):
            apply_revision(row=older, actor=self.reviewer, reason="Older export")

    def test_permission_and_reason(self):
        identity, event = self.drafted(nb_survivor="40")
        row = self.corrected(identity, nb_survivor="42")
        with self.assertRaises(PermissionDenied):
            apply_revision(row=row, actor=self.outsider, reason="r")
        with self.assertRaises(PermissionDenied):
            reject_revision(row=row, actor=self.outsider, reason="r")
        with self.assertRaises(ValidationError):
            apply_revision(row=row, actor=self.reviewer, reason="")
        self.assertFalse(EventRevision.objects.exists())


class RevisionReviewFindingTests(RevisionTestCase):
    """Regressions for the independent review of the revisions slice."""

    def test_zero_zero_correction_is_refused(self):
        identity, event = self.drafted(nb_survivor="40")
        row = self.corrected(identity, latitude="0", longitude="0")
        self.assertEqual(propose_revision(row).blocked_by, "position_to_review")
        with self.assertRaises(ValidationError):
            reject_revision(row=row, actor=self.reviewer, reason="Nothing computed")

    def test_alias_approved_after_drafting_is_not_a_hand_edit(self):
        identity, event = self.drafted(Port_disembarkation="Port fictif")
        self.assertIsNone(event.port)
        port = Port.objects.create(name="Port fictif")
        approve_port_alias(
            source=self.source, label="Port fictif", actor=self.reviewer, reason="r", ports=[port]
        )
        row = self.corrected(identity, Port_disembarkation="Port fictif", nb_survivor="7")
        proposal = propose_revision(row)
        self.assertEqual(proposal.conflicts, ())
        self.assertEqual(sorted(proposal.changes), ["people", "port"])
        apply_revision(row=row, actor=self.reviewer, reason="Port now known")
        event.refresh_from_db()
        self.assertEqual(event.port, port)

    def test_hand_edit_already_equal_to_the_correction_is_not_a_conflict(self):
        identity, event = self.drafted(nb_survivor="40")
        Event.objects.filter(pk=event.pk).update(people=42)
        row = self.corrected(identity, nb_survivor="42")
        self.assertEqual(propose_revision(row).conflicts, ())

    def test_regenerated_title_conflicts_with_a_hand_edited_date(self):
        identity, event = self.drafted(nb_survivor="40")
        Event.objects.filter(pk=event.pk).update(occurred_on="2024-02-10")
        row = self.corrected(identity, type_ops="Transfer")
        proposal = propose_revision(row)
        self.assertIn("title", proposal.conflicts)
        self.assertNotIn("occurred_on", proposal.changes)

    def test_hand_edited_title_conflicts_with_a_kind_change(self):
        identity, event = self.drafted(nb_survivor="40")
        Event.objects.filter(pk=event.pk).update(title="Edited title")
        row = self.corrected(identity, type_ops="Transfer")
        self.assertEqual(propose_revision(row).conflicts, ("title",))

    def test_conflicting_change_can_still_be_rejected_with_its_values(self):
        identity, event = self.drafted(nb_survivor="40")
        Event.objects.filter(pk=event.pk).update(people=41)
        row = self.corrected(identity, nb_survivor="42")
        revision = reject_revision(row=row, actor=self.reviewer, reason="Hand value is right")
        self.assertEqual(revision.changes, {"people": [40, 42]})

    def test_rejection_holds_for_the_same_change_only(self):
        identity, event = self.drafted(nb_survivor="40")
        f2 = self.corrected(identity, nb_survivor="42")
        reject_revision(row=f2, actor=self.reviewer, reason="Typo")
        f3 = self.corrected(identity, nb_survivor="43")
        apply_revision(row=f3, actor=self.reviewer, reason="Real correction")
        back = self.corrected(identity, nb_survivor=" 42")
        self.assertEqual(propose_revision(back).blocked_by, None)
        self.assertEqual(propose_revision(back).changes, {"people": (43, 42)})

    def test_nothing_to_reject_on_unchanged_or_stale_rows(self):
        identity, event = self.drafted(nb_survivor="40")
        with self.assertRaises(ValidationError):
            reject_revision(row=identity.drafted_from, actor=self.reviewer, reason="No change")
        older = self.corrected(identity, nb_survivor="42")
        self.corrected(identity, nb_survivor="44")
        with self.assertRaises(ValidationError):
            reject_revision(row=older, actor=self.reviewer, reason="Stale")

    def test_empty_revision_acknowledges_the_new_origin(self):
        identity, event = self.drafted(boat_type="Rubber")
        row = self.corrected(identity, boat_type="Wood")
        proposal = propose_revision(row)
        self.assertEqual((proposal.changes, proposal.blocked_by), ({}, None))
        revision = apply_revision(row=row, actor=self.reviewer, reason="Unmapped field only")
        self.assertEqual(revision.changes, {})
        identity.refresh_from_db()
        self.assertEqual(identity.drafted_from, row)
