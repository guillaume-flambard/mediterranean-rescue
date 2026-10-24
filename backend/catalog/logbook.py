"""The SOS MEDITERRANEE public logbook, read as rows of the operations sheet (ADR 0014).

The public map reads a Google Sheet last filled on 6 February 2024, while the crew keeps logging
every rotation of the Ocean Viking on sosmediterranee.org, entry by entry. This module reads those
pages politely (one request per second, identified, robots.txt allows it) and turns each rescue
completed by the Ocean Viking into a row in the sheet's exact column order, with the page, entry
and quote it comes from, and what a person should check. Nothing is guessed: a value the logbook
does not state stays empty.

Standard library only, so the same code runs in the backend (management command `sync_logbook`)
and as a stand-alone script (`scripts/logbook_backfill.py`).
"""

import csv
import hashlib
import html
import http.client
import io
import re
import time
import urllib.error
import urllib.request
import urllib.robotparser
import xml.etree.ElementTree as ET
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

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
_EN = "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty"
_FR = "un deux trois quatre cinq six sept huit neuf dix onze douze treize quatorze quinze seize dix-sept dix-huit dix-neuf vingt"
NUMBER_WORDS = {
    **{word: index for index, word in enumerate(_EN.split(), start=1)},
    **{word: index for index, word in enumerate(_FR.split(), start=1)},
    "une": 1,
}


# Fetching ------------------------------------------------------------------------------------


class ReadFailed(Exception):
    """A page could not be read completely: the whole reading fails rather than shrink."""


MAX_PAGE_BYTES = 3_000_000
PAGE_DEADLINE_SECONDS = 60


def _check_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise ReadFailed(f"refused address: {parsed.scheme}://{parsed.hostname}")


class _CheckedRedirects(urllib.request.HTTPRedirectHandler):
    # A redirect is followed only to https on the association's own hosts.
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _check_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _read_body(response) -> bytes:
    """At most MAX_PAGE_BYTES within a total deadline; a body shorter than announced is refused."""
    started = time.monotonic()
    chunks, size = [], 0
    while True:
        if time.monotonic() - started > PAGE_DEADLINE_SECONDS:
            raise ReadFailed("the page took too long")
        chunk = response.read(64 * 1024)
        if not chunk:
            break
        chunks.append(chunk)
        size += len(chunk)
        if size > MAX_PAGE_BYTES:
            raise ReadFailed("the page is larger than accepted")
    content = b"".join(chunks)
    announced = response.headers.get("Content-Length")
    if announced is not None and announced.isdigit() and int(announced) != len(content):
        raise ReadFailed("the page was cut before the end")
    return content


class Fetcher:
    """GET only, https on the association's hosts only (redirects too), one request per second,
    robots.txt respected, cached on disk when a cache directory is given."""

    def __init__(self, cache: Path | None = None, refresh: bool = False):
        self.cache = cache
        self.refresh = refresh
        self.last = 0.0
        self.robots: dict[str, urllib.robotparser.RobotFileParser] = {}
        self.opener = urllib.request.build_opener(_CheckedRedirects)
        if cache is not None:
            cache.mkdir(parents=True, exist_ok=True)

    def _download(self, url: str) -> str | None:
        wait = 1.0 - (time.monotonic() - self.last)
        if wait > 0:
            time.sleep(wait)
        self.last = time.monotonic()
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with self.opener.open(request, timeout=30) as response:
                return _read_body(response).decode("utf-8", "replace")
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return None
            raise

    def _allowed(self, url: str) -> bool:
        host = urlparse(url).hostname or ""
        if host not in self.robots:
            parser = urllib.robotparser.RobotFileParser()
            text = self._download(f"https://{host}/robots.txt") or ""
            parser.parse(text.splitlines())
            self.robots[host] = parser
        return self.robots[host].can_fetch(USER_AGENT, url)

    def get(self, url: str) -> str | None:
        """The page, or None when it does not exist (404). Anything else raises ReadFailed."""
        _check_url(url)
        path = (
            self.cache / (hashlib.sha256(url.encode()).hexdigest()[:24] + ".html")
            if self.cache is not None
            else None
        )
        if path is not None and path.exists() and not self.refresh:
            text = path.read_text()
            return text or None
        if not self._allowed(url):
            raise ReadFailed(f"robots.txt disallows {url}")
        try:
            text = self._download(url)
        except (urllib.error.URLError, OSError, http.client.HTTPException) as error:
            raise ReadFailed(f"{url}: {error.__class__.__name__}") from error
        if path is not None:
            path.write_text(text or "")
        return text


# Parsing helpers ------------------------------------------------------------------------------


def clean(fragment: str) -> str:
    text = re.sub(r"<(script|style)\b.*?</\1>", " ", fragment, flags=re.S | re.I)
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def make_date(year: int, month: int, day: int) -> date | None:
    """A calendar date, or None for an impossible one ("February 30") rather than a crash."""
    try:
        return date(year, month, day)
    except ValueError:
        return None


def parse_day(text: str) -> date | None:
    match = re.search(r"([A-Za-zéû]+)\s+(\d{1,2}),?\s+(\d{4})", text)
    if not match or match.group(1).lower() not in MONTHS:
        return None
    return make_date(int(match.group(3)), MONTHS[match.group(1).lower()], int(match.group(2)))


def count(word: str) -> int | None:
    """A number written in figures or words (English or French, up to twenty); None otherwise."""
    word = re.sub(r"[\s,]", "", word.lower())
    if word.isdigit():
        return int(word)
    return NUMBER_WORDS.get(word)


def to_sheet_coordinate(value: float) -> str:
    """The sheet writes degrees and decimal minutes without a hemisphere: 33° 25.00."""
    value = abs(value)
    degrees = int(value)
    minutes = round((value - degrees) * 60, 2)
    if minutes >= 60:  # 33.99999 rounds to 34° 00.00, not 33° 60.00
        degrees, minutes = degrees + 1, 0.0
    return f"{degrees}° {minutes:05.2f}"


def parse_position(text: str) -> tuple[float, float, str, str] | None:
    """Latitude and longitude in decimal degrees, with how they were read: "decimal", "text"
    (degrees and minutes written in the entry), "compact" (DDMM) or "swapped" (latitude and
    longitude inverted in the source).

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
        candidates.append((lat, lon, "text", re.sub(r"\s+", " ", match.group(0))))
    match = re.search(r"Latitude:\s*([\d.,]+)\s*/?\s*Longitude:\s*([\d.,]+)", text)
    if match:
        raw_lat, raw_lon = (part.replace(",", ".") for part in match.groups())
        for lat, lon, how in _read_pair(raw_lat, raw_lon):
            candidates.append((lat, lon, how, f"{raw_lat} {raw_lon}"))
    for lat, lon, how, raw in candidates:
        if 30 <= lat <= 40 and 8 <= lon <= 25:
            return lat, lon, how, raw
        if 30 <= lon <= 40 and 8 <= lat <= 25:
            return lon, lat, "swapped", raw
    return None


def _read_pair(raw_lat: str, raw_lon: str):
    try:
        lat, lon = float(raw_lat), float(raw_lon)
    except ValueError:
        return
    if "." in raw_lat or "." in raw_lon:
        yield lat, lon, "decimal"
    # Compact DDMM (3426 = 34° 26'), DDDMM for longitude (01209 = 12° 09').
    if raw_lat.isdigit() and raw_lon.isdigit() and len(raw_lat) == 4 and len(raw_lon) in (4, 5):
        yield (
            int(raw_lat[:2]) + int(raw_lat[2:]) / 60,
            int(raw_lon[:-2]) + int(raw_lon[-2:]) / 60,
            "compact",
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
        # Patterns run on a bounded text: a long hostile entry cannot make them backtrack.
        return f"{self.title} {self.body}".strip()[:4000]


@dataclass
class Rotation:
    slug: str
    url: str
    title: str = ""
    survivors: int | None = None
    port: str = ""
    entries: list = field(default_factory=list)


MAX_ENTRY_CHARS = 20_000


def parse_rotation_page(page: str) -> list[Entry]:
    entries = []
    day = None
    # Linear reading: cut the page at each day heading and entry, then read each piece on its
    # own (bounded), so a page with unclosed tags cannot make the patterns backtrack for minutes.
    markers = list(
        re.finditer(r'<h2 class="list-term-title|<article class="loop-item loop-item-log', page)
    )
    for index, marker in enumerate(markers):
        end = markers[index + 1].start() if index + 1 < len(markers) else len(page)
        piece = page[marker.start() : min(end, marker.start() + MAX_ENTRY_CHARS)]
        if piece.startswith("<h2"):
            heading = re.match(r'<h2 class="list-term-title[^"]*">([^<]{0,200})</h2>', piece)
            day = parse_day(clean(heading.group(1))) if heading else day
            continue
        block = piece
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
            flags.append(f"date_outside:{entry.day}")
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
                    flags + ["medevac"],
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
            flags.append("reported_in_message")
        # The same recovery is often logged twice on the same day with the same number: one row,
        # which says it merged a repeat, so two distinct rescues of equal size are not hidden.
        twin = next(
            (
                row
                for row in rows
                if row[0] == "Rescue" and row[1].day == entry.day and row[2] == people
            ),
            None,
        )
        if twin is not None:
            if "merged_repeat" not in twin[5]:
                twin[5].append("merged_repeat")
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
            flags.append(f"partial_replaced:{previous[2]}")
        where = position or (
            last_position[0] if last_position and last_position[1].day == entry.day else None
        )
        if not where:
            flags.append("no_position")
        elif where[2] != "decimal":
            flags.append(f"position_read:{where[2]}:{where[3]}")
        if re.search(r"two (?:simultaneous rescues|boats)|from two", text, re.I):
            flags.append("two_boats")
        rows.append(("Rescue", entry, people, where, last_boat, flags))
        last_boat = ""
    return rows


def _same_rescue(previous: Entry, entry: Entry) -> bool:
    return previous.day == entry.day


# French site, for rotations absent from the logbook -------------------------------------------


def french_rotations(get: Callable[[str], str | None], after: date):
    """Rescue summaries from the French "Sauvetages" feed, newest first."""
    items = []
    for page in range(1, 8):
        feed = get(FR_FEED.format(page=page))
        if not feed:
            break
        try:
            root = ET.fromstring(feed)
        except ET.ParseError as error:
            raise ReadFailed("the French rescue feed could not be read") from error
        found = root.findall("./channel/item")
        if not found:
            break
        for item in found:
            try:
                published = datetime.strptime(
                    item.findtext("pubDate", "")[:16], "%a, %d %b %Y"
                ).date()
            except ValueError:
                continue
            if published <= after:
                return items
            body = clean(
                item.findtext("{http://purl.org/rss/1.0/modules/content/}encoded", "")
                or item.findtext("description", "")
            )
            items.append((published, item.findtext("title", ""), item.findtext("link", ""), body))
    return items


# Codes for what a person should check, translated by the interface. Each is "code" or
# "code:value": date_outside:<day>, medevac, reported_in_message, partial_replaced:<n>, no_position,
# position_read:<text|compact|swapped>:<as written>, two_boats, news_site, grouped:<operations>,
# count_unknown, merged_repeat, rotation_total:<stated>/<found>.
CHECK_CODES = (
    "date_outside", "medevac", "reported_in_message", "partial_replaced", "no_position",
    "position_read", "two_boats", "news_site", "grouped", "count_unknown", "merged_repeat",
    "rotation_total",
)  # fmt: skip

FR_RESCUE = re.compile(
    r"(?:(?:porté secours|portée? secouru|secouru|secourues?)\D{0,40}?(\d{1,4})\s+personnes?|"
    r"(\d{1,4})\s+personnes\s+secourues)"
    r"(?:[^.]{0,80}?(?:lors\s+de|lors\s+d['’]|au\s+cours\s+de)\s+(\w+)\s+opérations?)?",
    re.I,
)
FR_PORT = re.compile(
    r"débarqu\w+[^.]{0,40}?\s(?:à|au port d['’]|au port de|dans le port de)\s*"
    r"([A-ZÉ][\w' -]+?)(?:[.,;(]|\s+(?:en|le|ce|dans|après|sur|au|,))",
)
FR_DATE = re.compile(
    r"(?:le|les|du|nuit du)\s+(\d{1,2})(?:er)?(?:\s+et\s+\d{1,2})?\s+(janvier|février|mars|avril|mai|"
    r"juin|juillet|août|septembre|octobre|novembre|décembre)(?:\s+(\d{4}))?",
    re.I,
)
FR_MONTHS = (
    "janvier", "fevrier", "février", "mars", "avril", "mai", "juin", "juillet", "aout", "août",
    "septembre", "octobre", "novembre", "decembre", "décembre",
)  # fmt: skip
FR_WOMEN = re.compile(
    r"\b(\d{1,3}|une|deux|trois|quatre|cinq|six|sept|huit|neuf|dix)\s+femmes\b", re.I
)
FR_MINORS = re.compile(
    r"\b(\d{1,3}|deux|trois|quatre|cinq|six|sept|huit|neuf|dix)\s+(?:enfants|mineur\.?e?\.?s|mineurs)\b",
    re.I,
)
FR_UNACCOMPANIED = re.compile(
    r"\b(\d{1,3}|un|une|deux|trois)\s+mineur\.?e?\.?s?\s+non\s+accompagn", re.I
)
FR_PREGNANT = re.compile(r"\b(\d{1,3}|une|deux|trois|quatre|cinq)\s+enceintes?\b", re.I)
FR_BOAT = {
    "pneumatique": "Rubber boat",
    "fibre de verre": "Fiberglass boat",
    "en fer": "Iron boat",
    "métallique": "Metal boat",
    "en bois": "Wooden boat",
}
# The sheet writes Italian port names; the French site writes them in French.
FR_PORTS = {
    "ancône": "Ancona", "ravenne": "Ravenna", "savone": "Savona", "salerne": "Salerno",
    "naples": "Napoli", "gênes": "Genova", "livourne": "Livorno", "syracuse": "Siracusa",
    "tarente": "Taranto", "pouzzoles": "Pozzuoli",
}  # fmt: skip


def excerpt(text: str, limit: int = 240) -> str:
    """A quote cut at a word boundary, with an ellipsis when shortened."""
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"(\b[lLdD]['’])\s+", r"\1", text)  # "l’ Ocean Viking" written with a stray space
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(",;:")
    return f"{cut}…"


def safe_link(url: str) -> bool:
    """Only https links on the association's hosts are kept and shown as links."""
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.hostname in ALLOWED_HOSTS


def french_row(published: date, title: str, link: str, body: str):
    """One row for a rotation the logbook does not hold, from its French news post.

    The post gives the rescue day, the people, the number of operations and often women and
    minors, the boat and the port, but no position: the row says so, and how many operations it
    groups, for a person to split or complete.
    """
    summary = body.split("Dernière mise à jour")[0]
    rescue = FR_RESCUE.search(summary) or FR_RESCUE.search(body)
    if not rescue:
        return None
    # The rescue day: in the post's address when it names one ("sauvetage-8-septembre"), else in
    # its first lines ("Le 24 mai 2026", "les 12 et 13 mai", "la nuit du 1er mai").
    slug = re.search(r"(\d{1,2})(?:er)?-(" + "|".join(FR_MONTHS) + r")(?:-(\d{4}))?", link.lower())
    day = slug or FR_DATE.search(summary)
    occurred = None
    if day:
        year = int(day.group(3)) if day.group(3) else published.year
        occurred = make_date(year, MONTHS[day.group(2).lower()], int(day.group(1)))
        # A live post is created when the mission starts, so the rescue may follow it by days; only
        # a day months ahead means the previous year (a January post about December).
        if occurred and (occurred - published).days > 60:
            occurred = make_date(year - 1, occurred.month, occurred.day)
    if occurred is None:
        # Without the rescue day the row would carry a guessed date: left to a person instead.
        return None
    people = rescue.group(1) or rescue.group(2)
    operations = count(rescue.group(3)) if rescue.group(3) else 1
    row = dict.fromkeys(SHEET_HEADER, "")
    row["date"] = occurred.strftime("%d/%m/%Y")
    row["type_ops"] = "Rescue"
    # An operation count written in words beyond what is read stays empty, never a default.
    row["nb_ops"] = "" if operations is None else str(operations)
    row["nb_survivor"] = people
    for name, pattern in (
        ("female", FR_WOMEN),
        ("under_18", FR_MINORS),
        ("under_18_unacc", FR_UNACCOMPANIED),
        ("pregnant_women", FR_PREGNANT),
    ):
        match = pattern.search(summary)
        value = count(match.group(1)) if match else None
        if value is not None:
            row[name] = str(value)
    for words, boat in FR_BOAT.items():
        if words in body.lower():
            row["boat_type"] = boat
            break
    port = FR_PORT.search(summary) or FR_PORT.search(body)
    if port:
        name = port.group(1).strip()
        row["Port_disembarkation"] = FR_PORTS.get(name.lower(), name)
    flags = ["news_site", "no_position"]
    if operations is None:
        flags.append("count_unknown")
    elif operations > 1:
        flags.append(f"grouped:{operations}")
    if (published - occurred).days > 10:
        flags.append(f"date_outside:{occurred}")
    provenance = {
        "rotation": title,
        "source_url": link,
        "entry": str(occurred),
        "quote": excerpt(summary),
        "to_check": "; ".join(flags),
    }
    return row, provenance


# Main -----------------------------------------------------------------------------------------


@dataclass
class Extraction:
    sheet_rows: list
    provenance: list
    summary: list
    others: list
    gaps: list

    @property
    def rescues(self):
        return [row for row in self.sheet_rows if row["type_ops"] == "Rescue"]


PORT_NAME = re.compile(r"^[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' .-]{1,60}$")


def extract(get: Callable[[str], str | None], after: date) -> Extraction:
    """Every rescue dated after `after`, as sheet rows with their provenance.

    A page that cannot be read makes the whole reading fail (ReadFailed): a partial reading
    would stage fewer rows and hide work already verified.
    """
    sitemap = get(f"{ORG}/operation-sitemap.xml")
    archive = get(f"{ORG}/operation-archived/")
    if not sitemap or not archive:
        raise ReadFailed("the list of rotations could not be read")
    urls = re.findall(
        r"<loc>(https://www\.sosmediterranee\.org/operation/[^<]{1,300})</loc>", sitemap
    )
    cards = {}
    for block in archive.split("<article")[1:]:
        block = block[:MAX_ENTRY_CHARS]
        link = re.search(r'href="(https://www\.sosmediterranee\.org/operation/[^"]{1,300})"', block)
        if not link:
            continue
        survivors = re.search(r"loop-item-survivors[^>]*>([^<]{0,100})<", block)
        port = re.search(r"loop-item-disembarkation[^>]*>([^<]{0,200})<", block)
        name = re.sub(r"(?i)^disembarkation:\s*", "", clean(port.group(1))) if port else ""
        cards[link.group(1).rstrip("/") + "/"] = (
            count(re.sub(r"\D", "", clean(survivors.group(1))) or "") if survivors else None,
            # Only a plausible place name is kept: anything else could be markup or a formula.
            name if PORT_NAME.match(name) else "",
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
            page = get(url if page_number == 1 else f"{url.rstrip('/')}/page/{page_number}/")
            if not page:
                if page_number == 1:
                    raise ReadFailed(f"the rotation page {slug} could not be read")
                break
            if page_number == 1:
                title = re.search(r"<title>([^<]{0,300})</title>", page)
                name = clean(title.group(1)).split("|")[0] if title else slug
                # Page titles end with the site name: "OPERATION 8-13 August 2026 - SOS MEDITERRANEE".
                rotation.title = re.sub(
                    r"\s*[-–]\s*SOS MEDITERRANEE\s*$", "", name, flags=re.I
                ).strip()
            entries = parse_rotation_page(page)
            if not entries:
                break
            rotation.entries.extend(entries)
            if len(entries) < 100:
                break
            page_number += 1
        rotations.append((rotation, rotation_window(slug, rotation.entries)))

    sheet_rows, provenance, summary, others = [], [], [], []
    for rotation, window in sorted(rotations, key=lambda item: item[1][0] or date.max):
        found = find_rescues(rotation, window)
        rescued = sum(people or 0 for kind, _, people, *_ in found if kind == "Rescue")
        matches = rotation.survivors == rescued
        # The rotation's stated total and its rows disagree: every row of it says so.
        total_flag = [] if matches else [f"rotation_total:{rotation.survivors}/{rescued}"]
        # The mission's dates name it, in the reader's language (the page titles vary).
        label = f"{window[0]}/{window[1]}" if window[0] and window[1] else rotation.title
        for kind, entry, people, where, boat, flags in found:
            if entry.day and entry.day <= after:
                continue  # already in the sheet
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
                        "quote": excerpt(entry.text),
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
                    "rotation": label,
                    "source_url": rotation.url,
                    "entry": f"{entry.day} {entry.time}".strip(),
                    "quote": excerpt(entry.text),
                    "to_check": "; ".join(flags + total_flag),
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
                "matches": "yes" if matches else "check",
            }
        )

    # Rotations the French site reports but the logbook does not hold: one row each, flagged.
    # Every logbook rotation counts as covered, including those already in the sheet.
    covered = [(item["first_day"], item["last_day"]) for item in summary if item["first_day"]]
    gaps = []
    for published, title, link, body in sorted(french_rotations(get, after)):
        if not safe_link(link):
            continue
        made = french_row(published, title, link, body)
        if made is None:
            # Not a rescue, or no rescue day (a body recovered, a statement): left to a person,
            # unless its publication falls within a mission the logbook already holds.
            if not any(start <= published <= end + timedelta(days=10) for start, end in covered):
                gaps.append({"published": published, "title": title, "source_url": link})
            continue
        row, origin = made
        rescued_on = date.fromisoformat(origin["entry"])
        if rescued_on <= after or any(start <= rescued_on <= end for start, end in covered):
            continue
        sheet_rows.append(row)
        provenance.append({"row": len(sheet_rows), **origin})

    # Rows in date order (the French ones were appended after the logbook's), renumbered.
    paired = sorted(
        zip(sheet_rows, provenance),
        key=lambda pair: (
            datetime.strptime(pair[0]["date"], "%d/%m/%Y") if pair[0]["date"] else datetime.max
        ),
    )
    sheet_rows = [row for row, _ in paired]
    provenance = [{**origin, "row": index} for index, (_, origin) in enumerate(paired, start=1)]
    return Extraction(sheet_rows, provenance, summary, others, gaps)


def rows_csv(rows) -> bytes:
    """The rows as a CSV in the sheet's column order, ready to be staged or pasted."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=SHEET_HEADER, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode()
