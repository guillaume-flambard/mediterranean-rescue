"""Scheduled reading of the SOS MEDITERRANEE public logbook into private staging (ADR 0014).

The operations sheet behind the public map stopped on 6 February 2024; the logbook did not. Each
reading rebuilds, from the logbook, the rows that come after the sheet's last operation and stages
them as a snapshot of their own source, next to the sheet's. Volunteers then verify them like any
other row; nothing is linked, drafted or published here. Each staged row keeps its evidence (page,
entry, quote, what to check).
"""

import logging
from datetime import date

from django.db import connection, transaction

from .crosswalk import stage_snapshot
from .logbook import Fetcher, extract, rows_csv
from .models import LogbookEvidence, SheetSnapshot, SheetSync, Source
from .sync import summarize, sync_actor

logger = logging.getLogger(__name__)

LOGBOOK_SOURCE_KEY = "sos-logbook"
LOGBOOK_SOURCE = {
    "name": "SOS MEDITERRANEE public logbook",
    "url": "https://www.sosmediterranee.org/operation-archived/",
}
SHEET = "Data_operations"
# One logbook reading at a time; a different key from the sheet reading.
ADVISORY_LOCK_KEY = 72_430_119
# Before any sheet was staged, the date the public map's sheet stopped (export of 24 October 2026).
SHEET_LAST_KNOWN = date(2024, 2, 6)


def logbook_source():
    source, _ = Source.objects.get_or_create(key=LOGBOOK_SOURCE_KEY, defaults=LOGBOOK_SOURCE)
    return source


def sheet_last_date():
    """The last operation in the sheet itself: only what comes after it is rebuilt."""
    last = None
    snapshots = (
        SheetSnapshot.objects.filter(sheet=SHEET)
        .exclude(source__key=LOGBOOK_SOURCE_KEY)
        .order_by("source_id", "-created_at")
        .distinct("source_id")
    )
    for snapshot in snapshots:
        for value in snapshot.rows.values_list("candidate__occurred_on", flat=True):
            if value and (last is None or value > last):
                last = value
    return date.fromisoformat(last) if last else SHEET_LAST_KNOWN


def _try_lock():
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_try_advisory_lock(%s)", [ADVISORY_LOCK_KEY])
        return cursor.fetchone()[0]


def _unlock():
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_unlock(%s)", [ADVISORY_LOCK_KEY])


def sync_logbook(*, actor=None, get=None):
    """One reading. Returns the SheetSync recorded, or None when another reading holds the lock."""
    if not _try_lock():
        return None
    try:
        source = logbook_source()
        actor = actor or sync_actor()
        try:
            result = extract(get or Fetcher().get, sheet_last_date())
        except Exception as exc:  # network, markup change: recorded, never fatal for the loop
            logger.warning("Logbook reading failed: %s", exc.__class__.__name__)
            return SheetSync.objects.create(
                source=source,
                sheet=SHEET,
                status="failed",
                message="The logbook could not be read.",
            )
        content = rows_csv(result.sheet_rows)
        with transaction.atomic():
            snapshot, created = stage_snapshot(
                source=source, sheet=SHEET, content=content, actor=actor
            )
            if created:
                rows = {row.line: row for row in snapshot.rows.all()}
                LogbookEvidence.objects.bulk_create(
                    [
                        LogbookEvidence(
                            row=rows[index + 2],
                            source_url=item["source_url"],
                            rotation=item["rotation"][:200],
                            logged_at=item["entry"][:40],
                            quote=item["quote"][:500],
                            to_check=item["to_check"],
                        )
                        for index, item in enumerate(result.provenance)
                        if index + 2 in rows
                    ]
                )
            return SheetSync.objects.create(
                source=source,
                sheet=SHEET,
                status="new_data" if created else "unchanged",
                snapshot=snapshot,
                sha256=snapshot.sha256,
                summary=summarize(snapshot),
            )
    finally:
        _unlock()
