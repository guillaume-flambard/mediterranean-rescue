#!/usr/bin/env python3
"""Rebuild the operations missing from the SOS MEDITERRANEE map from the association's own public
logbook (sosmediterranee.org), one row per rescue, with the source page of every value.

The public map reads a Google Sheet whose last operation is 6 February 2024. The logbook keeps
publishing every rotation of the Ocean Viking, entry by entry. This script reads it politely (one
request per second, identified, robots.txt allows it), keeps a local cache, and writes:

- Data_operations-backfill.csv: rows in the exact column order of the map's sheet, ready to be
  reviewed and pasted;
- backfill-provenance.csv: for every row, the page, the entry time and a short quote it comes from,
  and what still needs a human eye;
- backfill-rotations.csv: each rotation's stated total next to the sum of the rows found, so a
  missing rescue shows up;
- backfill-gaps.csv: rotations announced elsewhere (French site) but absent from the logbook;
- backfill-other-events.csv: events that are not rows of the sheet (transfers off the ship).

Nothing is guessed: a value the logbook does not state stays empty. Output goes to data/local/
(ignored by Git); the data belongs to SOS MEDITERRANEE and is not redistributed.

Usage: python3 scripts/logbook_backfill.py [--after 2024-02-06] [--out data/local/backfill]
"""

import argparse
import csv
import hashlib
import html
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
ORG = "https://www.sosmediterranee.org"
FR_FEED = "https://sosmediterranee.fr/categorie/sauvetages/feed/?paged={page}"
ALLOWED_HOSTS = {"www.sosmediterranee.org", "sosmediterranee.fr"}
USER_AGENT = (
    "mediterranean-rescue-backfill/0.1 (volunteer project; "
    "+https://github.com/guillaume-flambard/mediterranean-rescue)"
)
SHEET_HEADER = (
    "date,type_ops,nb_ops,nb_survivor,male,female,under_18,under_18_unacc,under_5,"
    "pregnant_women,latitude,longitude,wind_force,wave_height,boat_type,nb_nationalities,"
    "type_nationalities,transfer_type,Port_disembarkation,image_src,video_srv,"
    "testimony_name,testimony_src"
).split(",")
MONTHS = {
    name: number
    for number, names in enumerate(
        [
            ("january", "janvier"),
            ("february", "février", "fevrier"),
            ("march", "mars"),
            ("april", "avril"),
            ("may", "mai"),
            ("june", "juin"),
            ("july", "juillet"),
            ("august", "août", "aout"),
            ("september", "septembre"),
            ("october", "oktober", "octobre"),
            ("november", "novembre"),
            ("december", "décembre", "decembre"),
        ],
        start=1,
    )
    for name in names
}
NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
    "nine": 9, "ten": 10, "un": 1, "une": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5,
}  # fmt: skip


# Fetching ------------------------------------------------------------------------------------


class Fetcher:
    """GET only, allowed hosts only, one request per second, cached on disk."""

    def __init__(self, cache: Path, refresh: bool):
        self.cache = cache
        self.refresh = refresh
        self.last = 0.0
        cache.mkdir(parents=True, exist_ok=True)

    def get(self, url: str) -> str | None:
        host = urlparse(url).hostname
        if urlparse(url).scheme != "https" or host not in ALLOWED_HOSTS:
            raise ValueError(f"refused host: {host}")
        path = self.cache / (hashlib.sha256(url.encode()).hexdigest()[:24] + ".html")
        if path.exists() and not self.refresh:
            text = path.read_text()
            return text or None
        wait = 1.0 - (time.monotonic() - self.last)
        if wait > 0:
            time.sleep(wait)
        self.last = time.monotonic()
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                text = response.read(5_000_000).decode("utf-8", "replace")
        except urllib.error.HTTPError as error:
            if error.code == 404:
                path.write_text("")
                return None
            raise
        path.write_text(text)
        return text


# Parsing helpers ------------------------------------------------------------------------------


def clean(fragment: str) -> str:
    text = re.sub(r"<(script|style)\b.*?</\1>", " ", fragment, flags=re.S | re.I)
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def parse_day(text: str) -> date | None:
    match = re.search(r"([A-Za-zéû]+)\s+(\d{1,2}),?\s+(\d{4})", text)
    if not match or match.group(1).lower() not in MONTHS:
        return None
    return date(int(match.group(3)), MONTHS[match.group(1).lower()], int(match.group(2)))


def count(word: str) -> int | None:
    word = word.lower().replace(" ", "").replace(" ", "").replace(",", "")
    if word.isdigit():
        return int(word)
    return NUMBER_WORDS.get(word)


def to_sheet_coordinate(value: float) -> str:
    """The sheet writes degrees and decimal minutes without a hemisphere: 33° 25.00."""
    value = abs(value)
    degrees = int(value)
    minutes = (value - degrees) * 60
    return f"{degrees}° {minutes:05.2f}"


def parse_position(text: str) -> tuple[float, float, str] | None:
    """Latitude and longitude in decimal degrees, with how they were read.

    The logbook mixes formats: decimal degrees, degrees and minutes in the entry text
    ("34 23 N 012 59 E"), and compact DDMM ("3426 01209"). Central Mediterranean positions are
    north and east, between 30 and 40 N and 8 and 25 E; anything else is refused, not guessed.
    """
    candidates = []
    match = re.search(
        r"(\d{2})\s*°?\s*(\d{1,2}(?:[.,]\d+)?)\s*'?\s*N\b\W+0?(\d{1,2})\s*°?\s*(\d{1,2}(?:[.,]\d+)?)\s*'?\s*E\b",
        text,
    )
    if match:
        lat = int(match.group(1)) + float(match.group(2).replace(",", ".")) / 60
        lon = int(match.group(3)) + float(match.group(4).replace(",", ".")) / 60
        candidates.append((lat, lon, "degrees and minutes in the text"))
    match = re.search(r"Latitude:\s*([\d.,]+)\s*/?\s*Longitude:\s*([\d.,]+)", text)
    if match:
        raw_lat, raw_lon = (part.replace(",", ".") for part in match.groups())
        for lat, lon, how in _read_pair(raw_lat, raw_lon):
            candidates.append((lat, lon, how))
    for lat, lon, how in candidates:
        if 30 <= lat <= 40 and 8 <= lon <= 25:
            return lat, lon, how
        if 30 <= lon <= 40 and 8 <= lat <= 25:
            return lon, lat, how + ", latitude and longitude swapped in the source"
    return None


def _read_pair(raw_lat: str, raw_lon: str):
    try:
        lat, lon = float(raw_lat), float(raw_lon)
    except ValueError:
        return
    if "." in raw_lat or "." in raw_lon:
        yield lat, lon, "decimal degrees"
    # Compact DDMM (3426 = 34° 26'), DDDMM for longitude (01209 = 12° 09').
    if raw_lat.isdigit() and raw_lon.isdigit() and len(raw_lat) == 4 and len(raw_lon) in (4, 5):
        yield (
            int(raw_lat[:2]) + int(raw_lat[2:]) / 60,
            int(raw_lon[:-2]) + int(raw_lon[-2:]) / 60,
            "compact degrees and minutes",
        )


# Logbook --------------------------------------------------------------------------------------


@dataclass
class Entry:
    day: date | None
    time: str
    title: str
    body: str
    coordinates: str
    key_event: bool

    @property
    def text(self) -> str:
        return f"{self.title} {self.body}".strip()


@dataclass
class Rotation:
    slug: str
    url: str
    title: str = ""
    survivors: int | None = None
    port: str = ""
    entries: list = field(default_factory=list)


def parse_rotation_page(page: str) -> list[Entry]:
    entries = []
    day = None
    tokens = re.finditer(
        r'<h2 class="list-term-title[^"]*">(.*?)</h2>|<article class="loop-item loop-item-log[^"]*">(.*?)</article>',
        page,
        re.S,
    )
    for token in tokens:
        if token.group(1) is not None:
            day = parse_day(clean(token.group(1)))
            continue
        block = token.group(2)
        time_match = re.search(r'<span class="loop-item-time">\s*(.*?)\s*</span>', block, re.S)
        title_match = re.search(r'<div class="loop-item-title">(.*?)</div>', block, re.S)
        title = clean(title_match.group(1)) if title_match else ""
        when = clean(time_match.group(1)) if time_match else ""
        if when and title.startswith(when):
            title = title[len(when) :].strip()
        body_match = re.search(r'<div class="tinymce">(.*?)</div>\s*</div>', block, re.S)
        coords_match = re.search(
            r'<div class="loop-item-coordinates[^"]*">(.*?)</div>', block, re.S
        )
        entries.append(
            Entry(
                day=day,
                time=when,
                title=title,
                body=clean(body_match.group(1)) if body_match else "",
                coordinates=clean(coords_match.group(1)) if coords_match else "",
                key_event="loop-item-key-event" in block,
            )
        )
    return entries


def slug_window(slug: str) -> tuple[date | None, date | None]:
    """Dates written in the slug: "operation-14-23-march-2026", "25-december-2025-5-january-2026"."""
    found, pending = [], []
    for token in slug.lower().split("-"):
        if token.isdigit() and len(token) <= 2:
            pending.append(int(token))
        elif token in MONTHS:
            found += [[day, MONTHS[token], None] for day in pending]
            pending = []
        elif token.isdigit() and len(token) == 4:
            for item in found:
                if item[2] is None:
                    item[2] = int(token)
    try:
        dates = sorted(date(year, month, day) for day, month, year in found if year)
    except ValueError:
        return None, None
    return (dates[0], dates[-1]) if dates else (None, None)


def rotation_window(slug: str, entries: list[Entry]) -> tuple[date | None, date | None]:
    """The rotation's dates from its slug; from its entries when the slug is wrong or silent.

    Some pages carry a stray heading (an entry dated months later) and one slug names the wrong
    year, so the slug wins when most entries fall inside it, and the entries' middle half otherwise.
    """
    days = sorted(entry.day for entry in entries if entry.day)
    start, end = slug_window(slug)
    if start and days and sum(start <= day <= end for day in days) >= len(days) / 2:
        return start, end
    if not days:
        return start, end
    # The slug is wrong (one names 2024 for a 2025 rotation): the year most entries fall in.
    years = [day.year for day in days]
    year = max(set(years), key=years.count)
    inside = [day for day in days if day.year == year]
    return inside[0], inside[-1]


# A recovery completed by the Ocean Viking, in the wordings the logbook has used since 2024:
# "completes the recovery of 35", "Recovery completed. All 55 survivors safely on board",
# "Rescue operation AP0137 completed. 62 survivors", "safely embarks 97 survivors",
# "Ocean Viking rescues 38", "7 people are recovered from the water".
DONE = re.compile(
    r"complet\w*\s+(?:the|a)?\s*(?:recovery|rescue|evacuation)|"
    r"(?:recovery|rescue|evacuation)(?:\s+operation)?(?:\s+(?:of\s+)?(?:distress case\s+)?[A-Z]{2,3}\s?\d+)?\s+(?:is\s+)?completed|"
    r"safely\s+(?:embarks|recovered|brought)|rescues\s+\d|recovered\s+(?:from the water|on Ocean Viking)|"
    r"operated the rescue|\d+\s+(?:persons|people|survivors)\s+recovered",
    re.I,
)
# Messages the ship received or was copied on describe other vessels' rescues: never counted.
# The ship's own emails also put authorities "in copy", so only the ship being copied counts here.
OTHERS = re.compile(
    r"\b(?:receives?|is (?:in )?cop(?:y|ied)|in copy of|overhears|copied on)\b", re.I
)
# The ship reporting its own rescue in a message: counted, but marked for a human check.
REPORTED = re.compile(r"^(?:The\s+)?(?:Ocean Viking|OV)\s+(?:e-?mails|calls|sends|informs)\b", re.I)
PEOPLE = re.compile(
    r"\b(\d{1,4})\s+(?:shipwrecked\s+)?(?:persons?|people|survivors|shipwrecked|POB)\b", re.I
)
DEMOGRAPHICS = {
    "male": re.compile(r"(\d{1,4})\s+men\b", re.I),
    "female": re.compile(r"(\d{1,4})\s+women\b", re.I),
    "under_18": re.compile(r"(\d{1,4})\s+(?:children|minors)\b", re.I),
    "under_18_unacc": re.compile(r"(\d{1,4})\s+unaccompanied\s+minors\b", re.I),
}
BOAT = re.compile(
    r"\b((?:(?:white|grey|gray|black|blue|green|red|yellow|orange|brown|"
    r"metal|iron|wooden|rubber|fiberglass|fibreglass|and|/)\s+){1,5}(?:rubber|wooden|fiberglass|fibreglass|"
    r"metal|iron)\s+boat|(?:rubber|wooden|fiberglass|fibreglass|metal|iron)\s+boat)\b",
    re.I,
)
TRANSFER = re.compile(r"(?:transship\w*|transfer\w*)\D{0,60}?\b(\d{1,4})\b", re.I)
MEDEVAC = re.compile(r"medical evacuation|medevac", re.I)


def find_rescues(rotation: Rotation, window):
    """One row per recovery completed by the Ocean Viking, with the boat described before it."""
    rows = []
    start, end = window
    last_boat = ""
    last_position = None
    for entry in rotation.entries:
        text = entry.text
        boat = BOAT.search(text)
        if boat:
            last_boat = re.sub(r"\s+", " ", boat.group(1)).strip().capitalize()
        position = parse_position(f"{entry.coordinates} {text}")
        if position:
            last_position = (position, entry)
        flags = []
        if entry.day and start and end and not (start <= entry.day <= end):
            flags.append(f"date {entry.day} outside the rotation window {start} to {end}")
        lead = entry.title or text
        if OTHERS.search(lead[:80]):
            continue
        if MEDEVAC.search(text) and re.search(r"perform|complet|carried out", text, re.I):
            rows.append(
                (
                    "Medevac",
                    entry,
                    None,
                    None,
                    "",
                    flags + ["medical evacuation: check who and how many"],
                )
            )
            continue
        transfer = TRANSFER.search(text)
        if (
            transfer
            and re.search(r"transship|transfer", lead, re.I)
            and re.search(r"complet|perform|carried", text, re.I)
        ):
            rows.append(("Transfer", entry, int(transfer.group(1)), None, "", flags))
            continue
        # A disembarkation repeats the number of people already counted at the recovery.
        if not DONE.search(text) or re.search(r"disembark", text, re.I):
            continue
        people_match = PEOPLE.search(text)
        if not people_match:
            continue
        people = int(people_match.group(1))
        if REPORTED.search(lead):
            flags.append("only reported in a message from the ship: check it is not a duplicate")
        # The same recovery is often logged twice on the same day with the same number.
        if any(row[0] == "Rescue" and row[1].day == entry.day and row[2] == people for row in rows):
            continue
        # "RHIBs complete the recovery of 111", then "Ocean Viking completes the recovery all 129":
        # the second, saying all, is the whole recovery and replaces the partial count.
        if (
            re.search(r"\ball\s+\d", text, re.I)
            and rows
            and rows[-1][0] == "Rescue"
            and rows[-1][1].day == entry.day
            and (rows[-1][2] or 0) < people
        ):
            previous = rows.pop()
            flags.append(f"replaces a partial count of {previous[2]} logged just before")
        where = position or (
            last_position[0] if last_position and last_position[1].day == entry.day else None
        )
        if not where:
            flags.append("position not stated in the logbook")
        elif where[2] != "decimal degrees":
            flags.append(f"position read as {where[2]}")
        if re.search(r"two (?:simultaneous rescues|boats)|from two", text, re.I):
            flags.append(
                "one entry for two boats: split it into two rows if the sheet counts boats"
            )
        rows.append(("Rescue", entry, people, where, last_boat, flags))
        last_boat = ""
    return rows


def _same_rescue(previous: Entry, entry: Entry) -> bool:
    return previous.day == entry.day


# French site, for rotations absent from the logbook -------------------------------------------


def french_rotations(fetcher: Fetcher, after: date):
    """Rescue summaries from the French "Sauvetages" feed, newest first."""
    items = []
    for page in range(1, 8):
        feed = fetcher.get(FR_FEED.format(page=page))
        if not feed:
            break
        try:
            root = ET.fromstring(feed)
        except ET.ParseError:
            break
        found = root.findall("./channel/item")
        if not found:
            break
        for item in found:
            published = datetime.strptime(item.findtext("pubDate", "")[:16], "%a, %d %b %Y").date()
            if published <= after:
                return items
            body = clean(
                item.findtext("{http://purl.org/rss/1.0/modules/content/}encoded", "")
                or item.findtext("description", "")
            )
            items.append((published, item.findtext("title", ""), item.findtext("link", ""), body))
    return items


FR_RESCUE = re.compile(
    r"(?:porté secours|secouru|secourues?)\D{0,40}?(\d{1,4})\s+personnes?(?:[^.]{0,80}?(?:lors d['’]|en)\s+(\w+)\s+opérations?)?",
    re.I,
)
FR_PORT = re.compile(
    r"débarqu\w+\s+(?:à|au port de)\s+([A-Z][\w' -]+?)(?:[.,;]|\s+(?:en|le|ce|dans|après))", re.I
)


# Main -----------------------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--after", default="2024-02-06", help="last date already in the sheet")
    parser.add_argument("--out", default=str(ROOT / "data/local/backfill"))
    parser.add_argument(
        "--refresh", action="store_true", help="fetch again instead of using the cache"
    )
    args = parser.parse_args()
    after = date.fromisoformat(args.after)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    fetcher = Fetcher(ROOT / "data/local/logbook-cache", args.refresh)

    sitemap = fetcher.get(f"{ORG}/operation-sitemap.xml") or ""
    urls = re.findall(r"<loc>(https://www\.sosmediterranee\.org/operation/[^<]+)</loc>", sitemap)
    cards = {}
    archive = fetcher.get(f"{ORG}/operation-archived/") or ""
    for card in re.finditer(
        r'<article[^>]*class="[^"]*loop-item[^"]*"(.*?)</article>', archive, re.S
    ):
        block = card.group(1)
        link = re.search(r'href="(https://www\.sosmediterranee\.org/operation/[^"]+)"', block)
        if not link:
            continue
        survivors = re.search(r"loop-item-survivors[^>]*>(.*?)<", block, re.S)
        port = re.search(r"loop-item-disembarkation[^>]*>(.*?)<", block, re.S)
        cards[link.group(1).rstrip("/") + "/"] = (
            count(re.sub(r"\D", "", clean(survivors.group(1))) or "") if survivors else None,
            re.sub(r"(?i)^disembarkation:\s*", "", clean(port.group(1))) if port else "",
        )

    rotations = []
    for url in urls:
        slug = url.rstrip("/").rsplit("/", 1)[-1]
        if not re.search(r"20(2[4-9])", slug) or re.search(r"dry-?dock|detention", slug):
            continue
        rotation = Rotation(slug=slug, url=url)
        rotation.survivors, rotation.port = cards.get(url.rstrip("/") + "/", (None, ""))
        page_number = 1
        while True:
            page = fetcher.get(
                url if page_number == 1 else f"{url.rstrip('/')}/page/{page_number}/"
            )
            if not page:
                break
            if page_number == 1:
                title = re.search(r"<title>(.*?)</title>", page, re.S)
                rotation.title = clean(title.group(1)).split("|")[0].strip() if title else slug
            entries = parse_rotation_page(page)
            if not entries:
                break
            rotation.entries.extend(entries)
            if len(entries) < 100:
                break
            page_number += 1
        window = rotation_window(slug, rotation.entries)
        # A rotation that started on or before the sheet's last date is already in the sheet.
        if window[0] and window[0] <= after:
            continue
        rotations.append((rotation, window))

    sheet_rows, provenance, summary, others = [], [], [], []
    for rotation, window in sorted(rotations, key=lambda item: item[1][0] or date.max):
        found = find_rescues(rotation, window)
        rescued = 0
        for kind, entry, people, where, boat, flags in found:
            if kind == "Transfer":
                # The logbook's transfers move survivors off the Ocean Viking (to a coast guard
                # vessel); the sheet's Transfer rows count people taken on board from another ship.
                others.append(
                    {
                        "date": entry.day,
                        "what": "transfer off the Ocean Viking",
                        "people": people,
                        "rotation": rotation.title,
                        "source_url": rotation.url,
                        "quote": entry.text[:240],
                    }
                )
                continue
            row = dict.fromkeys(SHEET_HEADER, "")
            row["date"] = entry.day.strftime("%d/%m/%Y") if entry.day else ""
            row["type_ops"] = kind
            row["nb_ops"] = "1"
            if people is not None:
                row["nb_survivor"] = str(people)
            if kind == "Rescue":
                rescued += people or 0
                for name, pattern in DEMOGRAPHICS.items():
                    match = pattern.search(entry.text)
                    if match:
                        row[name] = match.group(1)
                row["boat_type"] = boat
                if where:
                    row["latitude"] = to_sheet_coordinate(where[0])
                    row["longitude"] = to_sheet_coordinate(where[1])
            row["Port_disembarkation"] = rotation.port
            sheet_rows.append(row)
            provenance.append(
                {
                    "row": len(sheet_rows),
                    "rotation": rotation.title,
                    "source_url": rotation.url,
                    "entry": f"{entry.day} {entry.time}",
                    "quote": entry.text[:240],
                    "to_check": "; ".join(flags),
                }
            )
        summary.append(
            {
                "rotation": rotation.title,
                "source_url": rotation.url,
                "first_day": window[0],
                "last_day": window[1],
                "port": rotation.port,
                "survivors_stated": "" if rotation.survivors is None else rotation.survivors,
                "survivors_in_rows": rescued,
                "rescue_rows": sum(1 for item in found if item[0] == "Rescue"),
                "matches": "yes" if rotation.survivors == rescued else "check",
            }
        )

    # Rotations the French site reports but the logbook does not hold.
    covered = [(item["first_day"], item["last_day"]) for item in summary if item["first_day"]]
    gaps = []
    for published, title, link, body in french_rotations(fetcher, after):
        if any(
            start <= published <= date.fromordinal(end.toordinal() + 10) for start, end in covered
        ):
            continue
        rescue = FR_RESCUE.search(body)
        port = FR_PORT.search(body)
        gaps.append(
            {
                "published": published,
                "title": title,
                "source_url": link,
                "people_rescued": rescue.group(1) if rescue else "",
                "operations": (count(rescue.group(2)) or "") if rescue and rescue.group(2) else "",
                "port": port.group(1).strip() if port else "",
            }
        )

    write(out / "Data_operations-backfill.csv", SHEET_HEADER, sheet_rows)
    write(
        out / "backfill-provenance.csv",
        ["row", "rotation", "source_url", "entry", "quote", "to_check"],
        provenance,
    )
    write(out / "backfill-rotations.csv", list(summary[0]) if summary else ["rotation"], summary)
    write(
        out / "backfill-other-events.csv",
        ["date", "what", "people", "rotation", "source_url", "quote"],
        others,
    )
    write(
        out / "backfill-gaps.csv",
        ["published", "title", "source_url", "people_rescued", "operations", "port"],
        gaps,
    )

    rescues = [row for row in sheet_rows if row["type_ops"] == "Rescue"]
    print(f"rotations read: {len(summary)}, rows: {len(sheet_rows)} ({len(rescues)} rescues)")
    print(f"people in rescue rows: {sum(int(row['nb_survivor'] or 0) for row in rescues)}")
    print(
        f"rotations whose rows match the stated total: {sum(1 for s in summary if s['matches'] == 'yes')}/{len(summary)}"
    )
    print(
        f"rows to check: {sum(1 for p in provenance if p['to_check'])}, rotations only on the French site: {len(gaps)}"
    )
    print(f"written to {out}")
    return 0


def write(path: Path, header, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    sys.exit(main())
