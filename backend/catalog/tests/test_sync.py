"""Scheduled reading of the Google Sheets exports (ADR 0012), with a fake network."""

import urllib.error

from django.test import Client

from catalog.models import Event, SheetSnapshot, SheetSync
from catalog.sync import FetchRefused, _check_url, sync_all
from catalog.tests.test_private_api import PrivateApiTestCase
from catalog.tests.test_sheets import ops_csv, ops_row

URL = "https://docs.google.com/spreadsheets/d/fictitious/export?format=csv&gid=0"


class SyncTests(PrivateApiTestCase):
    def config(self):
        return {"source": self.source.key, "tabs": {"Data_operations": URL}}

    def run_with(self, content):
        return sync_all(self.config(), actor=self.reviewer, fetch=lambda url, max_bytes: content)

    def test_new_data_is_staged_then_identical_bytes_are_unchanged(self):
        first = self.run_with(ops_csv(ops_row(), ops_row(date="04/02/2024")))[0]
        self.assertEqual(first.status, "new_data")
        self.assertEqual(
            first.summary, {"unchanged": 0, "to_look_at": 2, "to_fix": 0, "already_verified": 0}
        )
        again = self.run_with(ops_csv(ops_row(), ops_row(date="04/02/2024")))[0]
        self.assertEqual((again.status, again.snapshot_id), ("unchanged", first.snapshot_id))
        self.assertEqual(SheetSnapshot.objects.count(), 1)
        self.assertFalse(Event.objects.exists())

    def test_a_change_in_the_sheet_is_a_new_update(self):
        self.run_with(ops_csv(ops_row()))
        changed = self.run_with(ops_csv(ops_row(), ops_row(date="05/02/2024", nb_survivor="-1")))[0]
        self.assertEqual(changed.status, "new_data")
        self.assertEqual(changed.summary["to_fix"], 1)
        self.assertEqual(SheetSnapshot.objects.count(), 2)

    def test_a_cut_file_is_refused_and_an_unreachable_sheet_fails(self):
        refused = self.run_with(ops_csv(ops_row()) + b'"unterminated')[0]
        self.assertEqual(refused.status, "refused")
        self.assertIn(refused.message, ("read_partial", "read_rejected"))

        def down(url, max_bytes):
            raise urllib.error.URLError("offline")

        failed = sync_all(self.config(), actor=self.reviewer, fetch=down)[0]
        self.assertEqual(
            (failed.status, failed.message), ("failed", "The sheet could not be reached.")
        )
        self.assertFalse(SheetSnapshot.objects.exists())

    def test_only_google_export_addresses_are_read(self):
        _check_url(URL)
        _check_url("https://doc-0o-2g-sheets.googleusercontent.com/export/x")
        for url in (
            "http://docs.google.com/x",
            "https://example.org/x.csv",
            "https://docs.google.com.evil.test/x",
        ):
            with self.assertRaises(FetchRefused):
                _check_url(url)

    def test_status_endpoint_gives_times_and_counts_to_the_team(self):
        self.run_with(ops_csv(ops_row()))
        self.run_with(ops_csv(ops_row()))
        body = self.get("sync/").json()
        sheet = body["sheets"][0]
        self.assertEqual((sheet["sheet"], sheet["last_status"]), ("Data_operations", "unchanged"))
        self.assertEqual(sheet["last_change"]["to_look_at"], 1)
        self.assertIsNotNone(sheet["last_change_at"])
        self.assertEqual(self.get("sync/", client=Client()).status_code, 401)
        self.assertEqual(SheetSync.objects.count(), 2)
