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

    def test_without_a_mission_total_a_repeat_asks_for_a_check(self):
        _, rows = self.rows()
        self.assertIn("repeat_unsure:07:20", rows[0][5])
        self.assertFalse(any(flag.startswith("merged_repeat") for flag in rows[0][5]))

    def page_rows(self, entries, survivors):
        """Rows of a fictitious one-day rotation built from (time, text) entries."""
        page = '<h2 class="list-term-title contain--lg">March 13, 2025</h2>' + "".join(
            '<article class="loop-item loop-item-log"><div class="loop-item-title">'
            f'<span class="loop-item-time">{time}</span>{text}</div></article>'
            for time, text in entries
        )
        rotation = lb.Rotation(
            slug="operation-12-19-march-2025",
            url="https://www.sosmediterranee.org/operation/x/",
            survivors=survivors,
        )
        rotation.entries = lb.parse_rotation_page(page)
        return lb.find_rescues(rotation, lb.rotation_window(rotation.slug, rotation.entries))

    def test_the_repeat_of_a_replaced_partial_count_is_never_restored(self):
        # Review of 25 October 2026: 40 by the RHIBs, the same 40 again, then all 60.
        rows = self.page_rows(
            [
                ("05:00", "RHIBs complete the recovery of 40 shipwrecked persons."),
                ("05:10", "Recovery completed. 40 survivors on board."),
                ("06:00", "Ocean Viking completes the recovery all 60 shipwrecked persons."),
            ],
            survivors=100,
        )
        self.assertEqual([people for _, _, people, *_ in rows], [60])

    def test_a_repeat_neither_takes_nor_uses_up_the_next_boat(self):
        rows = self.page_rows(
            [
                ("05:00", "Ocean Viking completes the recovery of 40 shipwrecked persons."),
                ("06:00", "Ocean Viking observes a wooden boat."),
                ("06:30", "Recovery completed. 40 survivors on board."),
                ("08:00", "Ocean Viking completes the recovery of 30 shipwrecked persons."),
            ],
            survivors=110,
        )
        self.assertEqual(
            [(people, boat) for _, _, people, _, boat, _ in rows],
            [(40, ""), (40, ""), (30, "Wooden boat")],
        )

    def test_when_several_mentions_could_be_the_missing_rescue_none_is_chosen(self):
        # Two repeats of 40 and 40 people missing: which one is the second boat is a human call.
        rows = self.page_rows(
            [
                ("05:00", "Ocean Viking completes the recovery of 40 shipwrecked persons."),
                ("05:30", "Recovery completed. 40 survivors on board."),
                ("06:00", "All 40 survivors are now on board Ocean Viking, recovery completed."),
                ("09:00", "Ocean Viking completes the recovery of 25 shipwrecked persons."),
            ],
            survivors=105,
        )
        self.assertEqual([people for _, _, people, *_ in rows], [40, 25])
        self.assertIn("repeat_unsure:05:30", rows[0][5])
        self.assertIn("repeat_unsure:06:00", rows[0][5])

    # Data audit of 25 October 2026: cases the reader got wrong on the real logbook, rewritten
    # with fictitious entries.
    def test_a_message_that_is_the_only_record_of_a_rescue_counts(self):
        rows = self.page_rows(
            [
                (
                    "11:57",
                    "The Ocean Viking emails the authorities, informing about having operated the rescue of 46 people, and requests a Place of Safety for disembarktion.",
                )
            ],
            survivors=46,
        )
        self.assertEqual([(kind, people) for kind, _, people, *_ in rows], [("Rescue", 46)])
        self.assertIn("reported_in_message", rows[0][5])

    def test_a_message_about_disembarkation_after_the_rescue_does_not_count_again(self):
        rows = self.page_rows(
            [
                ("07:51", "Ocean Viking completes the rescue of 93 shipwrecked persons."),
                (
                    "08:45",
                    "Ocean Viking email the authorities about the completed rescue. Ocean Viking completed the recovery operation of the persons in distress. 94 persons, requests disembarkation.",
                ),
            ],
            survivors=93,
        )
        self.assertEqual([people for _, _, people, *_ in rows], [93])

    def test_people_taken_from_a_merchant_vessel_are_a_transfer_onto_the_ship(self):
        rows = self.page_rows(
            [
                ("11:28", "The Ocean Viking has visuals on the Merchant Vessel FICTIF."),
                ("13:48", "Evacuation completed: all 44 survivors on board the Ocean Viking."),
                (
                    "13:58",
                    "The Ocean Viking emails the authorities that the recovery operation is completed.",
                ),
            ],
            survivors=44,
        )
        self.assertEqual([(kind, people) for kind, _, people, *_ in rows], [("TransferIn", 44)])
        self.assertIn("transfer_to_ov", rows[0][5])

    def test_a_transfer_without_a_number_takes_what_the_mission_total_leaves(self):
        rows = self.page_rows(
            [
                ("07:00", "Ocean Viking completes the recovery of 20 shipwrecked persons."),
                ("12:43", "All survivors are successfully transshipped onto Ocean Viking."),
            ],
            survivors=53,
        )
        self.assertEqual(
            [(kind, people) for kind, _, people, *_ in rows], [("Rescue", 20), ("TransferIn", 33)]
        )
        self.assertIn("count_from_total:33", rows[1][5])
        self.assertNotIn("count_unknown", rows[1][5])

    def test_a_named_case_takes_its_own_position_and_boat_never_another_case(self):
        rows = self.page_rows(
            [
                (
                    "03:34",
                    "The Ocean Viking completes the recovery operation of distress case AP0095 and safely embarks 97 survivors on board.",
                ),
                (
                    "03:35",
                    "The Ocean Viking emails the authorities transmitting FINAL SITREP regarding distress case AP0095: at 0235 UTC in position 34 57 N 012 05 E the recovery was completed.",
                ),
                (
                    "11:23",
                    "The Ocean Viking overhears a Mayday Relay regarding distress case ADC018 involving a blue wooden boat with 80 persons on board.",
                ),
                (
                    "13:13",
                    "The Ocean Viking is copied on an email regarding distress case ADC019 involving 30 persons on board a black rubber boat. Latitude: 34.5 / Longitude: 12.5",
                ),
                (
                    "13:30",
                    "The Ocean Viking completes the recovery operation for distress case ADC018 and safely embarks 50 survivors on board.",
                ),
            ],
            survivors=147,
        )
        first, second = rows
        self.assertEqual((round(first[3][0], 2), round(first[3][1], 2)), (34.95, 12.08))
        self.assertIn("position_from:03:35", first[5])
        self.assertIsNone(second[3])
        self.assertEqual(second[4], "Blue wooden boat")

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
