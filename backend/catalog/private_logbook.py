"""The public logbook as the way to bring the SOS map up to date (ADR 0014).

`GET logbook/` says how far the sheet lags behind the logbook and how much of the rebuilt rows the
team has verified. `GET logbook/export/` gives the verified rows as a CSV in the sheet's own column
order, ready to be pasted into the sheet that feeds the public map. Nothing is written to the sheet
or published from here.
"""

import csv
import io

from django.http import HttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers
from rest_framework.response import Response

from .api import parameters
from .crosswalk import propose_links
from .logbook import SHEET_HEADER
from .logbook_sync import (
    LOGBOOK_SOURCE_KEY,
    SHEET,
    current_logbook_snapshot,
    rows_already_in_sheet,
    sheet_last_date,
)
from .models import SheetSnapshot, SheetSync
from .private_api import ERRORS, STATUS_BY_PROPOSAL, CanStageOrReview, PrivateView


def latest_logbook_snapshot():
    return current_logbook_snapshot()


def sheet_cell(value):
    """A cell safe to paste into a spreadsheet: one starting like a formula is kept as text."""
    text = "" if value is None else str(value)
    return f"'{text}" if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


def for_the_sheet(row):
    """Rows the SOS sheet holds: rescues and transfers with a number of people. The sheet has no
    medical evacuation, and its map adds up nb_survivor without a guard, so a row without a number
    would break its monthly chart (CartONG SOSMedDashboard, src/components/Chart.vue)."""
    candidate = row.candidate or {}
    return candidate.get("kind") in ("rescue", "transfer") and bool(candidate.get("nb_survivor"))


def row_statuses(snapshot):
    return {p.row_id: STATUS_BY_PROPOSAL[p.kind] for p in propose_links(snapshot)}


# People rescued per year as SOS MEDITERRANEE published them in its annual reports, to check the
# sheet plus the rebuilt rows against (sosmediterranee.fr/publications, read 24 October 2026).
REPORTED_PEOPLE = {2024: 1948, 2025: 1358}
REPORTS_URL = "https://sosmediterranee.fr/publications/"
# People rescued since 2016 as the association's home page gave them (sosmediterranee.fr, read
# 24 October 2026). Rows after this date are not part of the comparison.
REPORTED_CUMULATIVE = ("2026-10-02", 43641)


class LogbookYearSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    in_sheet = serializers.IntegerField()
    from_logbook = serializers.IntegerField()
    reported = serializers.IntegerField(allow_null=True)


class LogbookCumulativeSerializer(serializers.Serializer):
    as_of = serializers.DateField()
    reported = serializers.IntegerField()
    in_sheet = serializers.IntegerField()
    from_logbook = serializers.IntegerField(help_text="Rebuilt rescues up to as_of.")
    after = serializers.IntegerField(
        help_text="People in rebuilt rescues after as_of, not compared."
    )


class LogbookOverviewSerializer(serializers.Serializer):
    sheet_last_date = serializers.DateField()
    last_read_at = serializers.DateTimeField(allow_null=True)
    last_read_status = serializers.CharField(allow_blank=True)
    first_date = serializers.CharField(allow_null=True)
    last_date = serializers.CharField(allow_null=True)
    rows = serializers.IntegerField()
    people = serializers.IntegerField()
    verified = serializers.IntegerField()
    to_verify = serializers.IntegerField()
    to_fix = serializers.IntegerField()
    to_check = serializers.IntegerField(help_text="Rows whose evidence asks for a human check.")
    in_sheet = serializers.IntegerField(
        help_text="Rebuilt rows the association's sheet now holds; left out of the export."
    )
    ready = serializers.IntegerField(help_text="Verified rows not in the sheet yet: the export.")
    not_for_sheet = serializers.IntegerField(
        help_text="Rows the sheet does not hold (medical evacuations, no number of people)."
    )
    snapshot = serializers.UUIDField(allow_null=True)
    years = LogbookYearSerializer(many=True)
    cumulative = LogbookCumulativeSerializer(allow_null=True)
    reports_url = serializers.URLField()


def _people_by_year(rows, kinds=("rescue", "transfer")):
    totals = {}
    for row in rows:
        candidate = row.candidate or {}
        day, people = candidate.get("occurred_on"), candidate.get("nb_survivor")
        if day and people and candidate.get("kind") in kinds:
            totals[int(day[:4])] = totals.get(int(day[:4]), 0) + people
    return totals


def _sheet_people_by_year():
    sheet = {}
    for snapshot in (
        # Fictitious training sources never count against SOS's reports.
        SheetSnapshot.objects.filter(sheet=SHEET, source__synthetic=False)
        .exclude(source__key=LOGBOOK_SOURCE_KEY)
        .order_by("source_id", "-created_at")
        .distinct("source_id")
    ):
        for year, people in _people_by_year(snapshot.rows.all()).items():
            sheet[year] = sheet.get(year, 0) + people
    return sheet


def cumulative_total(logbook_rows, sheet):
    """Everyone in the sheet plus the rescues rebuilt up to the date of SOS's published total."""
    as_of, reported = REPORTED_CUMULATIVE
    before = after = 0
    for row in logbook_rows:
        candidate = row.candidate or {}
        day, people = candidate.get("occurred_on"), candidate.get("nb_survivor")
        if day and people and candidate.get("kind") == "rescue":
            if day <= as_of:
                before += people
            else:
                after += people
    return {
        "as_of": as_of,
        "reported": reported,
        "in_sheet": sum(sheet.values()),
        "from_logbook": before,
        "after": after,
    }


def year_totals(logbook_rows, sheet=None):
    """For each year the logbook covers: people in the sheet, rebuilt, and as SOS reported them."""
    sheet = _sheet_people_by_year() if sheet is None else sheet
    rebuilt = _people_by_year(logbook_rows, kinds=("rescue",))
    return [
        {
            "year": year,
            "in_sheet": sheet.get(year, 0),
            "from_logbook": rebuilt.get(year, 0),
            "reported": REPORTED_PEOPLE.get(year),
        }
        for year in sorted(rebuilt)
    ]


class LogbookOverviewView(PrivateView):
    permission_classes = [CanStageOrReview]

    @extend_schema(
        responses={200: LogbookOverviewSerializer, **ERRORS}, operation_id="private_logbook"
    )
    def get(self, request):
        parameters(request, serializers.Serializer)
        snapshot = latest_logbook_snapshot()
        last_read = (
            SheetSync.objects.filter(source__key=LOGBOOK_SOURCE_KEY).order_by("-created_at").first()
        )
        payload = {
            "sheet_last_date": sheet_last_date(),
            "last_read_at": last_read.created_at if last_read else None,
            "last_read_status": last_read.status if last_read else "",
            "first_date": None,
            "last_date": None,
            "rows": 0,
            "people": 0,
            "verified": 0,
            "to_verify": 0,
            "to_fix": 0,
            "to_check": 0,
            "in_sheet": 0,
            "ready": 0,
            "not_for_sheet": 0,
            "snapshot": None,
            "years": [],
            "cumulative": None,
            "reports_url": REPORTS_URL,
        }
        if snapshot is not None:
            statuses = row_statuses(snapshot)
            rows = list(snapshot.rows.select_related("logbook"))
            dates = sorted(
                row.candidate["occurred_on"]
                for row in rows
                if row.candidate and row.candidate.get("occurred_on")
            )
            payload.update(
                first_date=dates[0] if dates else None,
                last_date=dates[-1] if dates else None,
                rows=len(rows),
                people=sum((row.candidate or {}).get("nb_survivor") or 0 for row in rows),
                verified=sum(1 for row in rows if statuses[row.pk] == "linked"),
                to_verify=sum(1 for row in rows if statuses[row.pk] == "to_review"),
                to_fix=sum(1 for row in rows if statuses[row.pk] == "blocked"),
                to_check=sum(
                    1 for row in rows if hasattr(row, "logbook") and row.logbook.to_check.strip()
                ),
                snapshot=snapshot.pk,
            )
            in_sheet = rows_already_in_sheet(rows)
            payload.update(
                in_sheet=len(in_sheet),
                ready=sum(
                    1
                    for row in rows
                    if statuses[row.pk] == "linked"
                    and row.pk not in in_sheet
                    and for_the_sheet(row)
                ),
                not_for_sheet=sum(1 for row in rows if not for_the_sheet(row)),
            )
            sheet = _sheet_people_by_year()
            payload.update(years=year_totals(rows, sheet), cumulative=cumulative_total(rows, sheet))
        return Response(LogbookOverviewSerializer(payload).data)


class LogbookExportView(PrivateView):
    permission_classes = [CanStageOrReview]

    @extend_schema(
        responses={
            (200, "text/csv"): OpenApiResponse(
                OpenApiTypes.STR, description="Verified rows in the sheet's column order."
            ),
            **ERRORS,
        },
        operation_id="private_logbook_export",
    )
    def get(self, request):
        parameters(request, serializers.Serializer)
        snapshot = latest_logbook_snapshot()
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(snapshot.header_cells if snapshot else SHEET_HEADER)
        if snapshot is not None:
            statuses = row_statuses(snapshot)
            rows = list(snapshot.rows.order_by("line"))
            in_sheet = rows_already_in_sheet(rows)
            # Only rows a volunteer verified, as the logbook rebuilt them, in date order, and never
            # a row the association has already pasted into its sheet.
            for row in rows:
                if statuses[row.pk] == "linked" and row.pk not in in_sheet and for_the_sheet(row):
                    writer.writerow([sheet_cell(cell) for cell in row.raw_cells])
        response = HttpResponse(buffer.getvalue(), content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = (
            'attachment; filename="Data_operations-from-logbook-verified.csv"'
        )
        response["Cache-Control"] = "no-store"
        return response
