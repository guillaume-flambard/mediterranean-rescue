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
from .logbook_sync import LOGBOOK_SOURCE_KEY, SHEET, current_logbook_snapshot, sheet_last_date
from .models import SheetSnapshot, SheetSync
from .private_api import ERRORS, STATUS_BY_PROPOSAL, CanStageOrReview, PrivateView


def latest_logbook_snapshot():
    return current_logbook_snapshot()


def sheet_cell(value):
    """A cell safe to paste into a spreadsheet: one starting like a formula is kept as text."""
    text = "" if value is None else str(value)
    return f"'{text}" if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


def row_statuses(snapshot):
    return {p.row_id: STATUS_BY_PROPOSAL[p.kind] for p in propose_links(snapshot)}


# People rescued per year as SOS MEDITERRANEE published them in its annual reports, to check the
# sheet plus the rebuilt rows against (sosmediterranee.fr/publications, read 24 October 2026).
REPORTED_PEOPLE = {2024: 1948, 2025: 1358}
REPORTS_URL = "https://sosmediterranee.fr/publications/"


class LogbookYearSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    in_sheet = serializers.IntegerField()
    from_logbook = serializers.IntegerField()
    reported = serializers.IntegerField(allow_null=True)


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
    snapshot = serializers.UUIDField(allow_null=True)
    years = LogbookYearSerializer(many=True)
    reports_url = serializers.URLField()


def _people_by_year(rows, kinds=("rescue", "transfer")):
    totals = {}
    for row in rows:
        candidate = row.candidate or {}
        day, people = candidate.get("occurred_on"), candidate.get("nb_survivor")
        if day and people and candidate.get("kind") in kinds:
            totals[int(day[:4])] = totals.get(int(day[:4]), 0) + people
    return totals


def year_totals(logbook_rows):
    """For each year the logbook covers: people in the sheet, rebuilt, and as SOS reported them."""
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
            "snapshot": None,
            "years": [],
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
                years=year_totals(rows),
            )
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
            # Only rows a volunteer verified, as the logbook rebuilt them, in date order.
            for row in snapshot.rows.order_by("line"):
                if statuses[row.pk] == "linked":
                    writer.writerow([sheet_cell(cell) for cell in row.raw_cells])
        response = HttpResponse(buffer.getvalue(), content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = (
            'attachment; filename="Data_operations-from-logbook-verified.csv"'
        )
        response["Cache-Control"] = "no-store"
        return response
