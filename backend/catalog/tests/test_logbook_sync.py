"""The public logbook read into staging, shown with its evidence and exported for the sheet
(ADR 0014). A fictitious site stands in for sosmediterranee.org; real PostGIS."""

from django.test import Client

from catalog.crosswalk import approve_link
from catalog.logbook_sync import LOGBOOK_SOURCE_KEY, sheet_last_date, sync_logbook
from catalog.models import LogbookEvidence, SheetSync, Source
from catalog.tests.test_private_api import PrivateApiTestCase
from catalog.tests.test_sheets import ops_csv, ops_row

ORG = "https://www.sosmediterranee.org"
ROTATION = f"{ORG}/operation/operation-12-19-march-2025/"
SITE = {
    f"{ORG}/operation-sitemap.xml": f"<urlset><url><loc>{ROTATION}</loc></url></urlset>",
    f"{ORG}/operation-archived/": f"""
        <article class="loop-item"><a href="{ROTATION}">x</a>
        <span class="loop-item-survivors">65 survivors</span>
        <span class="loop-item-disembarkation">disembarkation: Port fictif</span></article>""",
    ROTATION: """<title>OPERATION 12-19 March 2025 (fictitious) | SOS</title>
        <h2 class="list-term-title contain--lg">March 13, 2025</h2>
        <article class="loop-item loop-item-log"><div class="loop-item-title">
        <span class="loop-item-time">05:10</span>Ocean Viking observes a white rubber boat.</div>
        <div class="loop-item-coordinates">Latitude: 33.5 / Longitude: 12.25</div></article>
        <article class="loop-item loop-item-log"><div class="loop-item-title">
        <span class="loop-item-time">07:00</span>
        Ocean Viking completes the recovery of 40 shipwrecked persons.</div></article>
        <h2 class="list-term-title contain--lg">March 14, 2025</h2>
        <article class="loop-item loop-item-log"><div class="loop-item-title">
        <span class="loop-item-time">12:30</span>
        Ocean Viking completes the recovery of 25 shipwrecked persons.</div></article>""",
}


def fake_site(url):
    return SITE.get(url)


class LogbookSyncTests(PrivateApiTestCase):
    def setUp(self):
        super().setUp()
        # The sheet stops on 6 February 2024, as the real one does.
        self.stage(ops_csv(ops_row(date="06/02/2024")))

    def read(self):
        return sync_logbook(actor=self.reviewer, get=fake_site)

    def test_rebuilds_the_rows_after_the_sheet_with_their_evidence(self):
        self.assertEqual(str(sheet_last_date()), "2024-02-06")
        run = self.read()
        self.assertEqual(run.status, "new_data")
        source = Source.objects.get(key=LOGBOOK_SOURCE_KEY)
        self.assertFalse(source.rights_approved)
        rows = list(run.snapshot.rows.order_by("line"))
        self.assertEqual([row.candidate["nb_survivor"] for row in rows], [40, 25])
        self.assertEqual(rows[0].candidate["Port_disembarkation"], "Port fictif")
        evidence = LogbookEvidence.objects.get(row=rows[0])
        self.assertEqual(evidence.source_url, ROTATION)
        self.assertIn("completes the recovery of 40", evidence.quote)
        # The same logbook read again is not a new update.
        self.assertEqual(self.read().status, "unchanged")
        self.assertEqual(SheetSync.objects.filter(source=source).count(), 2)

    def test_a_site_that_cannot_be_read_is_recorded_not_fatal(self):
        def broken(url):
            raise OSError("down")

        run = sync_logbook(actor=self.reviewer, get=broken)
        self.assertEqual(run.status, "failed")
        self.assertFalse(LogbookEvidence.objects.exists())

    def test_the_team_sees_the_quote_and_can_show_only_the_logbook(self):
        self.read()
        body = self.get(f"preview/events/?source={LOGBOOK_SOURCE_KEY}").json()
        self.assertEqual(body["total_count"], 2)
        first = body["items"][0]
        self.assertEqual(first["source"]["key"], LOGBOOK_SOURCE_KEY)
        self.assertEqual(first["evidence"]["url"], ROTATION)
        self.assertIn("recovery of 25", first["evidence"]["quote"])
        sheet_rows = self.get("preview/events/?source=fixture").json()
        self.assertEqual(sheet_rows["total_count"], 1)
        self.assertIsNone(sheet_rows["items"][0]["evidence"])

    def test_overview_and_export_of_verified_rows_only(self):
        run = self.read()
        overview = self.get("logbook/").json()
        self.assertEqual(
            {key: overview[key] for key in ("rows", "people", "verified", "to_verify")},
            {"rows": 2, "people": 65, "verified": 0, "to_verify": 2},
        )
        self.assertEqual(overview["sheet_last_date"], "2024-02-06")
        response = self.get("logbook/export/")
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertEqual(response.content.decode().count("\n"), 1)  # header only
        approve_link(row=run.snapshot.rows.get(line=2), actor=self.reviewer, reason="Checked")
        lines = self.get("logbook/export/").content.decode().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith("date,type_ops,nb_ops,nb_survivor"))
        self.assertTrue(lines[1].startswith("13/03/2025,Rescue,1,40"))
        self.assertEqual(self.get("logbook/").json()["verified"], 1)

    def test_reviewers_only(self):
        self.assertEqual(self.get("logbook/", client=Client()).status_code, 401)
        outsider = Client()
        outsider.force_login(self.outsider)
        self.assertEqual(self.get("logbook/export/", client=outsider).status_code, 403)
