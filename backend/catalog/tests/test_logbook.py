"""Offline tests of the logbook reader, on fictitious entries written like the real logbook."""

from datetime import date

from django.test import SimpleTestCase

from catalog import logbook as lb

# Fictitious rotation page, built like the logbook's HTML.
PAGE = """
<h2 class="list-term-title contain--lg">March 13, 2025</h2>
<article class="loop-item loop-item-log"><div class="loop-item-title"><span class="loop-item-time">05:10</span>
Ocean Viking observes an overcrowded white rubber boat.</div>
<div class="tinymce"><p>The white rubber boat is unseaworthy.</p></div></div>
<div class="loop-item-coordinates">Latitude: 33.5 / Longitude: 12.25</div></article>
<article class="loop-item loop-item-log"><div class="loop-item-title"><span class="loop-item-time">07:00</span>
Ocean Viking completes the recovery of 40 shipwrecked persons.</div></article>
<article class="loop-item loop-item-log"><div class="loop-item-title"><span class="loop-item-time">07:20</span>
Recovery completed. All 40 survivors safely on board Ocean Viking: 30 men, 6 women and 4 children.</div></article>
<article class="loop-item loop-item-log"><div class="loop-item-title"><span class="loop-item-time">09:00</span>
Ocean Viking is in copy of an email from another vessel that completed the rescue of 70 people.</div></article>
<h2 class="list-term-title contain--lg">March 14, 2025</h2>
<article class="loop-item loop-item-log"><div class="loop-item-title"><span class="loop-item-time">12:00</span>
RHIBs complete the recovery of 20 shipwrecked persons.</div></article>
<article class="loop-item loop-item-log"><div class="loop-item-title"><span class="loop-item-time">12:30</span>
Ocean Viking completes the recovery all 25 shipwrecked persons in position 34 23 N 012 59 E.</div></article>
<h2 class="list-term-title contain--lg">March 18, 2025</h2>
<article class="loop-item loop-item-log"><div class="loop-item-title"><span class="loop-item-time">10:00</span>
Disembarkation of the 65 survivors starts.</div></article>
"""


class ReaderTests(SimpleTestCase):
    def rows(self):
        rotation = lb.Rotation(
            slug="operation-12-19-march-2025", url="https://www.sosmediterranee.org/operation/x/"
        )
        rotation.entries = lb.parse_rotation_page(PAGE)
        window = lb.rotation_window(rotation.slug, rotation.entries)
        return window, lb.find_rescues(rotation, window)

    def test_one_row_per_recovery_and_none_for_other_ships_or_disembarkation(self):
        window, rows = self.rows()
        self.assertEqual(window, (date(2025, 3, 12), date(2025, 3, 19)))
        self.assertEqual(
            [(kind, people) for kind, _, people, *_ in rows], [("Rescue", 40), ("Rescue", 25)]
        )

    def test_the_boat_and_position_described_before_the_recovery_are_kept(self):
        _, rows = self.rows()
        kind, entry, people, where, boat, flags = rows[0]
        self.assertEqual(boat, "White rubber boat")
        self.assertEqual((round(where[0], 2), round(where[1], 2)), (33.5, 12.25))
        self.assertEqual(lb.to_sheet_coordinate(where[0]), "33° 30.00")

    def test_a_total_saying_all_replaces_the_partial_count_before_it(self):
        _, rows = self.rows()
        flags = rows[1][5]
        self.assertTrue(any("partial count of 20" in flag for flag in flags))
        self.assertTrue(any("degrees and minutes" in flag for flag in flags))

    def test_positions_in_every_format_and_nothing_outside_the_region(self):
        self.assertEqual(
            lb.parse_position("Latitude: 3426 / Longitude: 01209")[2], "compact degrees and minutes"
        )
        swapped = lb.parse_position("Latitude: 13.75 / Longitude: 34.27")
        self.assertEqual((swapped[0], swapped[1]), (34.27, 13.75))
        self.assertIsNone(lb.parse_position("Latitude: 48.85 / Longitude: 2.35"))

    def test_slug_dates_and_a_wrong_slug_year(self):
        self.assertEqual(
            lb.slug_window("operation-25-december-2025-5-january-2026"),
            (date(2025, 12, 25), date(2026, 1, 5)),
        )
        entries = [lb.Entry(date(2025, 7, day), "", "x", "", "", False) for day in (1, 2, 6)]
        self.assertEqual(
            lb.rotation_window("25-june-06-july-2024", entries),
            (date(2025, 7, 1), date(2025, 7, 6)),
        )
