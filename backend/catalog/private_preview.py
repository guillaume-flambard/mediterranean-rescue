"""Private preview of the latest exports on the main screen (ADR 0011).

Read-only: rows of the latest Data_operations and Other_data snapshots of each source, as the
map and the list would show them, with their review state. Nothing is created or published, and
only signed-in reviewers can read it.
"""

from django.http import Http404
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response

from .api import parameters
from .crosswalk import propose_links
from .logbook_sync import LOGBOOK_SOURCE_KEY, current_logbook_snapshot, rows_already_in_sheet
from .models import SheetRow, SheetSnapshot, Source
from .private_api import (
    ERRORS,
    STATUS_BY_PROPOSAL,
    STATUSES,
    LogbookEvidenceSerializer,
    PageParams,
    PrivateView,
    logbook_evidence,
    page,
)

PREVIEW_SHEETS = ("Data_operations", "Other_data")
MAX_POINTS = 2000


class PreviewFilters(serializers.Serializer):
    start = serializers.DateField(required=False)
    end = serializers.DateField(required=False)
    kind = serializers.CharField(required=False, max_length=40)
    status = serializers.ChoiceField(choices=STATUSES, required=False)
    q = serializers.CharField(required=False, max_length=80)
    # A source key, e.g. the public logbook ("sos-logbook"): only that source's rows.
    source = serializers.SlugField(required=False, max_length=50)

    def validate(self, attrs):
        if "start" in attrs and "end" in attrs and attrs["start"] > attrs["end"]:
            raise serializers.ValidationError({"end": "The end date is before the start date."})
        return attrs


class PreviewPageParams(PageParams, PreviewFilters):
    pass


def latest_snapshots():
    snapshots = []
    for source in Source.objects.order_by("name"):
        if source.key == LOGBOOK_SOURCE_KEY:
            # The logbook's rows are those of its last successful reading (ADR 0014).
            snapshot = current_logbook_snapshot()
            if snapshot is not None:
                snapshots.append(snapshot)
            continue
        for sheet in PREVIEW_SHEETS:
            snapshot = (
                SheetSnapshot.objects.filter(source=source, sheet=sheet)
                .select_related("source")
                .order_by("-created_at")
                .first()
            )
            if snapshot is not None:
                snapshots.append(snapshot)
    return snapshots


def position(candidate):
    value = (candidate or {}).get("position")
    if not value:
        return None
    longitude, latitude = float(value["longitude"]), float(value["latitude"])
    if longitude == 0 and latitude == 0:
        return None
    formats = f"{value.get('latitude_format', '')}{value.get('longitude_format', '')}"
    return {
        "longitude": longitude,
        "latitude": latitude,
        "inferred_hemisphere": "inferred" in formats,
    }


def item(row, snapshot, status, in_sheet=None):
    candidate = row.candidate or {}
    images = candidate.get("image_src") or []
    return {
        "id": row.pk,
        "snapshot": snapshot.pk,
        "sheet": snapshot.sheet,
        "line": row.line,
        "exported_at": snapshot.created_at,
        "source": {"key": snapshot.source.key, "name": snapshot.source.name},
        "synthetic": snapshot.source.synthetic,
        "status": status,
        "error_codes": row.error_codes,
        "occurred_on": candidate.get("occurred_on"),
        "kind": candidate.get("kind"),
        "people": candidate.get("nb_survivor"),
        "men": candidate.get("male"),
        "women": candidate.get("female"),
        "minors": candidate.get("under_18"),
        "deaths": candidate.get("death_nb_people"),
        "port_label": candidate.get("Port_disembarkation"),
        "boat_type": candidate.get("boat_type"),
        "position": position(candidate),
        "image_count": len(images) if isinstance(images, list) else 0,
        "evidence": logbook_evidence(row, in_sheet),
    }


def preview_items(values):
    """Every previewed row matching the filters, newest event first."""
    items = []
    for snapshot in latest_snapshots():
        if "source" in values and snapshot.source.key != values["source"]:
            continue
        statuses = {p.row_id: STATUS_BY_PROPOSAL[p.kind] for p in propose_links(snapshot)}
        rows = list(
            snapshot.rows.select_related("logbook").only(
                "id", "line", "candidate", "error_codes", "logbook"
            )
        )
        in_sheet = rows_already_in_sheet(rows) if snapshot.source.key == LOGBOOK_SOURCE_KEY else {}
        for row in rows:
            entry = item(row, snapshot, statuses[row.pk], in_sheet)
            day = entry["occurred_on"]
            if "start" in values and (day is None or day < values["start"].isoformat()):
                continue
            if "end" in values and (day is None or day > values["end"].isoformat()):
                continue
            if "kind" in values and entry["kind"] != values["kind"]:
                continue
            if "status" in values and entry["status"] != values["status"]:
                continue
            # Every word must appear in the port or boat as written in the export.
            text = f"{entry['port_label'] or ''} {entry['boat_type'] or ''}".casefold()
            if any(word.casefold() not in text for word in values.get("q", "").split()):
                continue
            items.append(entry)
    # Unknown dates last, then by line so the order is stable.
    items.sort(key=lambda entry: (entry["occurred_on"] or "", -entry["line"]), reverse=True)
    return items


class PreviewSourceSerializer(serializers.Serializer):
    key = serializers.CharField()
    name = serializers.CharField()


class PreviewPositionSerializer(serializers.Serializer):
    longitude = serializers.FloatField()
    latitude = serializers.FloatField()
    inferred_hemisphere = serializers.BooleanField()


class PreviewItemSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    snapshot = serializers.UUIDField()
    sheet = serializers.CharField()
    line = serializers.IntegerField()
    exported_at = serializers.DateTimeField()
    source = PreviewSourceSerializer()
    synthetic = serializers.BooleanField()
    status = serializers.ChoiceField(choices=STATUSES)
    error_codes = serializers.ListField(child=serializers.CharField())
    occurred_on = serializers.CharField(allow_null=True)
    kind = serializers.CharField(allow_null=True)
    people = serializers.IntegerField(allow_null=True)
    men = serializers.IntegerField(allow_null=True)
    women = serializers.IntegerField(allow_null=True)
    minors = serializers.IntegerField(allow_null=True)
    deaths = serializers.IntegerField(allow_null=True)
    port_label = serializers.CharField(allow_null=True)
    boat_type = serializers.CharField(allow_null=True)
    position = PreviewPositionSerializer(allow_null=True)
    image_count = serializers.IntegerField()
    evidence = LogbookEvidenceSerializer(allow_null=True)


class PreviewCountsSerializer(serializers.Serializer):
    to_review = serializers.IntegerField()
    blocked = serializers.IntegerField()
    linked = serializers.IntegerField()


class PreviewPageSerializer(serializers.Serializer):
    items = PreviewItemSerializer(many=True)
    total_count = serializers.IntegerField()
    has_next = serializers.BooleanField()
    counts = PreviewCountsSerializer()


class PreviewPointSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    longitude = serializers.FloatField()
    latitude = serializers.FloatField()
    kind = serializers.CharField(allow_null=True)
    status = serializers.ChoiceField(choices=STATUSES)


class PreviewMapSerializer(serializers.Serializer):
    points = PreviewPointSerializer(many=True)
    located_count = serializers.IntegerField()
    truncated = serializers.BooleanField()


class PreviewEventsView(PrivateView):
    @extend_schema(
        parameters=[PreviewPageParams],
        responses={200: PreviewPageSerializer, **ERRORS},
        operation_id="private_preview_events",
    )
    def get(self, request):
        values = parameters(request, PreviewPageParams)
        items = preview_items(values)
        counts = dict.fromkeys(STATUSES, 0)
        for entry in items:
            counts[entry["status"]] += 1
        return Response(PreviewPageSerializer({**page(values, items), "counts": counts}).data)


class PreviewMapView(PrivateView):
    @extend_schema(
        parameters=[PreviewFilters],
        responses={200: PreviewMapSerializer, **ERRORS},
        operation_id="private_preview_map_points",
    )
    def get(self, request):
        located = [
            entry
            for entry in preview_items(parameters(request, PreviewFilters))
            if entry["position"]
        ]
        points = [
            {
                "id": entry["id"],
                "longitude": entry["position"]["longitude"],
                "latitude": entry["position"]["latitude"],
                "kind": entry["kind"],
                "status": entry["status"],
            }
            for entry in located[:MAX_POINTS]
        ]
        return Response(
            PreviewMapSerializer(
                {
                    "points": points,
                    "located_count": len(located),
                    "truncated": len(located) > MAX_POINTS,
                }
            ).data
        )


class PreviewEventView(PrivateView):
    @extend_schema(
        responses={200: PreviewItemSerializer, **ERRORS}, operation_id="private_preview_event"
    )
    def get(self, request, id):
        parameters(request, serializers.Serializer)
        row = SheetRow.objects.select_related("snapshot__source", "logbook").filter(pk=id).first()
        latest = {snapshot.pk for snapshot in latest_snapshots()}
        if row is None or row.snapshot_id not in latest:
            raise Http404
        status = next(
            STATUS_BY_PROPOSAL[p.kind] for p in propose_links(row.snapshot) if p.row_id == row.pk
        )
        return Response(PreviewItemSerializer(item(row, row.snapshot, status)).data)


class PreviewTimelineFilters(serializers.Serializer):
    kind = serializers.CharField(required=False, max_length=40)
    status = serializers.ChoiceField(choices=STATUSES, required=False)
    q = serializers.CharField(required=False, max_length=80)
    source = serializers.SlugField(required=False, max_length=50)


class PreviewMonthSerializer(serializers.Serializer):
    month = serializers.CharField()
    count = serializers.IntegerField()


class PreviewTimelineSerializer(serializers.Serializer):
    months = PreviewMonthSerializer(many=True)
    undated = serializers.IntegerField(help_text="Rows without a usable date, left off the months.")


class PreviewTimelineView(PrivateView):
    @extend_schema(
        parameters=[PreviewTimelineFilters],
        responses={200: PreviewTimelineSerializer, **ERRORS},
        operation_id="private_preview_timeline",
    )
    def get(self, request):
        counts = {}
        undated = 0
        for entry in preview_items(parameters(request, PreviewTimelineFilters)):
            if entry["occurred_on"]:
                month = entry["occurred_on"][:7]
                counts[month] = counts.get(month, 0) + 1
            else:
                undated += 1
        months = [{"month": month, "count": counts[month]} for month in sorted(counts)]
        return Response(PreviewTimelineSerializer({"months": months, "undated": undated}).data)
