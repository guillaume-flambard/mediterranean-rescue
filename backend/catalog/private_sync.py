"""Freshness of the Google Sheets readings for the team (ADR 0012): counts and times, no values."""

from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response

from .api import parameters
from .models import SHEETS, SheetSnapshot, SheetSync
from .private_api import ERRORS, CanStageOrReview, PrivateView
from .sync import summarize

STATUSES = ("new_data", "unchanged", "refused", "failed")


class SyncSheetSerializer(serializers.Serializer):
    sheet = serializers.ChoiceField(choices=SHEETS)
    source = serializers.CharField()
    last_checked_at = serializers.DateTimeField()
    last_status = serializers.ChoiceField(choices=STATUSES)
    last_message = serializers.CharField(allow_blank=True)
    last_change_at = serializers.DateTimeField(allow_null=True)
    last_change = serializers.DictField(child=serializers.IntegerField())


class SyncStatusSerializer(serializers.Serializer):
    sheets = SyncSheetSerializer(many=True)


class SyncStatusView(PrivateView):
    permission_classes = [CanStageOrReview]

    @extend_schema(
        responses={200: SyncStatusSerializer, **ERRORS}, operation_id="private_sync_status"
    )
    def get(self, request):
        parameters(request, serializers.Serializer)
        sheets = []
        pairs = SheetSync.objects.values_list("source_id", "sheet").distinct().order_by("sheet")
        for source_id, sheet in pairs:
            runs = SheetSync.objects.filter(source_id=source_id, sheet=sheet).select_related(
                "source"
            )
            last = runs.order_by("-created_at").first()
            # The latest saved update, whether the scheduled reading or a person added it.
            latest = (
                SheetSnapshot.objects.filter(source_id=source_id, sheet=sheet)
                .order_by("-created_at")
                .first()
            )
            sheets.append(
                {
                    "sheet": sheet,
                    "source": last.source.name,
                    "last_checked_at": last.created_at,
                    "last_status": last.status,
                    "last_message": last.message,
                    "last_change_at": latest.created_at if latest else None,
                    "last_change": summarize(latest) if latest else {},
                }
            )
        return Response(SyncStatusSerializer({"sheets": sheets}).data)
