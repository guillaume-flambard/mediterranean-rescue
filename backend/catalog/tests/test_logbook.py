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
    def rows(self, survivors=None):
        rotation = lb.Rotation(
            slug="operation-12-19-march-2025",
            url="https://www.sosmediterranee.org/operation/x/",
            survivors=survivors,
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
        self.assertIn("partial_replaced:20", flags)
        self.assertIn("position_read:text:34 23 N 012 59 E", flags)

    def test_a_repeat_is_counted_once_when_the_mission_total_agrees(self):
        _, rows = self.rows(survivors=65)
        self.assertEqual([people for _, _, people, *_ in rows], [40, 25])
        self.assertIn("merged_repeat:07:20", rows[0][5])

    def test_two_rescues_of_the_same_size_stay_two_when_the_mission_total_says_so(self):
        # Audit of 25 October 2026: a second boat with as many people must never vanish.
        _, rows = self.rows(survivors=105)
        self.assertEqual([people for _, _, people, *_ in rows], [40, 40, 25])
        self.assertEqual([row[1].time for row in rows], ["07:00", "07:20", "12:30"])
        for row in rows[:2]:
            self.assertIn("same_size_twice", row[5])
            self.assertFalse(any(flag.startswith("merged_repeat") for flag in row[5]))

    def test_positions_in_every_format_and_nothing_outside_the_region(self):
        self.assertEqual(lb.parse_position("Latitude: 3426 / Longitude: 01209")[2], "compact")
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

    def test_every_note_is_a_known_code(self):
        _, rows = self.rows()
        for *_, flags in rows:
            for flag in flags:
                self.assertIn(flag.split(":")[0], lb.CHECK_CODES)


class FrenchPostTests(SimpleTestCase):
    """Rotations absent from the logbook, read from the French news posts (fictitious text)."""

    def test_a_post_becomes_one_flagged_row(self):
        body = (
            "Le 7 octobre, les équipes à bord de l’ Ocean Viking ont porté secours à 101 personnes "
            "lors de deux opérations distinctes. Parmi elles se trouvent 28 femmes, dont cinq "
            "enceintes, et 28 enfants, dont 16 mineur.e.s non accompagné.e.s, à bord d’une "
            "embarcation pneumatique. L’ Ocean Viking a débarqué les personnes rescapées à Naples "
            "le 10 octobre. Dernière mise à jour le 10/10/2026 ..."
        )
        row, origin = lb.french_row(
            date(2026, 10, 7),
            "Fictitious post",
            "https://sosmediterranee.fr/sauvetages/sauvetage-7-octobre/",
            body,
        )
        self.assertEqual(
            {
                key: row[key]
                for key in (
                    "date",
                    "nb_ops",
                    "nb_survivor",
                    "female",
                    "under_18",
                    "under_18_unacc",
                    "pregnant_women",
                )
            },
            {
                "date": "07/10/2026",
                "nb_ops": "2",
                "nb_survivor": "101",
                "female": "28",
                "under_18": "28",
                "under_18_unacc": "16",
                "pregnant_women": "5",
            },
        )
        self.assertEqual(
            (row["boat_type"], row["Port_disembarkation"], row["latitude"]),
            ("Rubber boat", "Napoli", ""),
        )
        self.assertEqual(origin["to_check"], "news_site; no_position; grouped:2")

    def test_the_rescue_day_comes_from_the_address_and_a_statement_is_not_a_row(self):
        body = "Vendredi 11 septembre, les 78 personnes secourues par l’Ocean Viking, lors de trois opérations de sauvetage, ont débarqué à Salerne."
        row, _ = lb.french_row(
            date(2026, 9, 9),
            "x",
            "https://sosmediterranee.fr/sauvetages/sauvetage-8-septembre/",
            body,
        )
        self.assertEqual(
            (row["date"], row["nb_ops"], row["nb_survivor"], row["Port_disembarkation"]),
            ("08/09/2026", "3", "78", "Salerno"),
        )
        self.assertIsNone(
            lb.french_row(
                date(2026, 1, 30),
                "x",
                "https://sosmediterranee.fr/x/",
                "Un corps sans vie a été récupéré.",
            )
        )


class ReaderSafetyTests(SimpleTestCase):
    def test_redirects_leave_only_for_the_association_hosts(self):
        handler = lb._CheckedRedirects()
        with self.assertRaises(lb.ReadFailed):
            handler.redirect_request(
                None, None, 302, "Found", {}, "http://www.sosmediterranee.org/x"
            )
        with self.assertRaises(lb.ReadFailed):
            handler.redirect_request(None, None, 302, "Found", {}, "https://evil.example/x")

    def test_hostile_text_stays_fast_and_unknown_counts_stay_empty(self):
        import time

        started = time.monotonic()
        entry = lb.Entry(date(2025, 3, 13), "", "transfer " * 20_000, "", "", False)
        rotation = lb.Rotation(slug="operation-12-19-march-2025", url="x")
        rotation.entries = [entry]
        lb.find_rescues(rotation, (date(2025, 3, 12), date(2025, 3, 19)))
        lb.parse_rotation_page('<article class="loop-item loop-item-log">' + "<div " * 200_000)
        self.assertLess(time.monotonic() - started, 3)
        self.assertEqual((lb.count("sept"), lb.count("dix-huit"), lb.count("cent")), (7, 18, None))
        body = "Le 3 mai 2026, l’Ocean Viking a porté secours à 40 personnes lors de cent opérations, dont sept femmes. Dernière mise à jour"
        row, origin = lb.french_row(date(2026, 5, 4), "x", "https://sosmediterranee.fr/a/", body)
        self.assertEqual((row["nb_ops"], row["female"]), ("", "7"))
        self.assertIn("count_unknown", origin["to_check"])

    def test_links_dates_and_coordinates_never_invent(self):
        self.assertFalse(lb.safe_link("javascript:alert(1)"))
        self.assertFalse(lb.safe_link("http://sosmediterranee.fr/x"))
        self.assertTrue(lb.safe_link("https://sosmediterranee.fr/x"))
        self.assertIsNone(lb.make_date(2024, 2, 30))
        self.assertIsNone(lb.parse_day("February 30, 2024"))
        self.assertEqual(lb.to_sheet_coordinate(33.99999), "34° 00.00")
        self.assertIsNone(
            lb.french_row(
                date(2026, 5, 4),
                "x",
                "https://sosmediterranee.fr/a/",
                "40 personnes secourues, sans date.",
            )
        )
        self.assertTrue(lb.excerpt("mot " * 100).endswith("…"))
