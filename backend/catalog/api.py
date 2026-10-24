from django.conf import settings
from django.contrib.gis.geos import Polygon
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_field
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.views import exception_handler as default_exception_handler

from .models import Event, EventKind, Evidence, Port, Source, Vessel, Voyage


class ErrorSerializer(serializers.Serializer):
    code = serializers.CharField()
    detail = serializers.CharField()
    errors = serializers.JSONField(required=False)


def exception_handler(exc, context):
    response = default_exception_handler(exc, context)
    if response is not None:
        original = response.data
        response.data = {
            "code": f"http_{response.status_code}",
            "detail": "Request rejected",
            "errors": original,
        }
    return response


ERRORS = {400: ErrorSerializer, 404: ErrorSerializer, 405: ErrorSerializer, 413: ErrorSerializer}


class Filters(serializers.Serializer):
    start = serializers.DateField(required=False)
    end = serializers.DateField(required=False)
    kind = serializers.ChoiceField(choices=EventKind.choices, required=False)
    bbox = serializers.CharField(required=False, help_text="west,south,east,north in WGS84")

    def validate(self, attrs):
        if attrs.get("start") and attrs.get("end") and attrs["start"] > attrs["end"]:
            raise ValidationError({"end": "Must not precede start"})
        if "bbox" in attrs:
            try:
                west, south, east, north = map(float, attrs["bbox"].split(","))
                if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
                    raise ValueError
            except (ValueError, TypeError):
                raise ValidationError({"bbox": "Use west,south,east,north within WGS84 bounds"})
            attrs["bbox"] = (west, south, east, north)
        return attrs


class PageFilters(Filters):
    limit = serializers.IntegerField(min_value=1, max_value=100, default=25)
    offset = serializers.IntegerField(min_value=0, max_value=100000, default=0)


class EvidenceFilters(serializers.Serializer):
    limit = serializers.IntegerField(min_value=1, max_value=100, default=25)
    offset = serializers.IntegerField(min_value=0, max_value=100000, default=0)


def parameters(request, serializer_type):
    allowed = serializer_type().fields
    if any(
        key not in allowed or len(request.query_params.getlist(key)) != 1
        for key in request.query_params
    ):
        raise ValidationError({"query": "Unknown or repeated parameter"})
    serializer = serializer_type(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


def filtered_events(values):
    queryset = Event.objects.public()
    if "start" in values:
        queryset = queryset.filter(occurred_on__gte=values["start"])
    if "end" in values:
        queryset = queryset.filter(occurred_on__lte=values["end"])
    if "kind" in values:
        queryset = queryset.filter(kind=values["kind"])
    if "bbox" in values:
        queryset = queryset.filter(location__intersects=Polygon.from_bbox(values["bbox"]))
    return queryset


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ("id", "name", "url", "license_note", "synthetic")

        read_only_fields = fields


class VesselSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vessel
        fields = ("id", "name", "imo")

        read_only_fields = fields


class PortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Port
        fields = ("id", "name", "country_code")

        read_only_fields = fields


class VoyageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voyage
        fields = ("id", "title", "started_on", "ended_on", "logbook_url")

        read_only_fields = fields


class PositionSerializer(serializers.Serializer):
    longitude = serializers.FloatField()
    latitude = serializers.FloatField()
    precision = serializers.CharField()


class EventSerializer(serializers.ModelSerializer):
    source = SourceSerializer()
    vessel = VesselSerializer(allow_null=True)
    voyage = VoyageSerializer(allow_null=True)
    port = PortSerializer(allow_null=True)
    position = serializers.SerializerMethodField()

    @extend_schema_field(PositionSerializer(allow_null=True))
    def get_position(self, obj):
        if obj.location is None:
            return None
        return {
            "longitude": obj.location.x,
            "latitude": obj.location.y,
            "precision": obj.location_precision,
        }

    class Meta:
        model = Event
        fields = (
            "id",
            "title",
            "summary",
            "occurred_on",
            "kind",
            "people",
            "women",
            "minors",
            "source_url",
            "source",
            "vessel",
            "voyage",
            "port",
            "position",
        )

        read_only_fields = fields


class EvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evidence
        fields = ("id", "label", "url")

        read_only_fields = fields


class EventPageSerializer(serializers.Serializer):
    items = EventSerializer(many=True)
    total_count = serializers.IntegerField()
    has_next = serializers.BooleanField()
    data_mode = serializers.ChoiceField(choices=["production", "training"])


class EvidencePageSerializer(serializers.Serializer):
    items = EvidenceSerializer(many=True)
    total_count = serializers.IntegerField()
    has_next = serializers.BooleanField()


class MapPointSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    longitude = serializers.FloatField()
    latitude = serializers.FloatField()
    kind = serializers.ChoiceField(choices=EventKind.choices)


class MapResultSerializer(serializers.Serializer):
    points = MapPointSerializer(many=True)
    located_count = serializers.IntegerField()
    truncated = serializers.BooleanField()


class PublicView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    http_method_names = ["get", "head", "options"]

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "no-store"
        return response


class EventsView(PublicView):
    @extend_schema(
        parameters=[PageFilters],
        responses={200: EventPageSerializer, **ERRORS},
        operation_id="list_events",
    )
    def get(self, request):
        values = parameters(request, PageFilters)
        queryset = filtered_events(values).select_related("source", "vessel", "voyage", "port")
        count = queryset.count()
        offset, limit = values["offset"], values["limit"]
        return Response(
            {
                "items": EventSerializer(queryset[offset : offset + limit], many=True).data,
                "total_count": count,
                "has_next": offset + limit < count,
                "data_mode": settings.DATA_MODE,
            }
        )


class EventView(PublicView):
    @extend_schema(responses={200: EventSerializer, **ERRORS}, operation_id="retrieve_event")
    def get(self, request, id):
        parameters(request, serializers.Serializer)
        event = get_object_or_404(
            Event.objects.public().select_related("source", "vessel", "voyage", "port"), pk=id
        )
        return Response(EventSerializer(event).data)


class EvidenceView(PublicView):
    @extend_schema(
        parameters=[EvidenceFilters],
        responses={200: EvidencePageSerializer, **ERRORS},
        operation_id="list_event_evidence",
    )
    def get(self, request, id):
        values = parameters(request, EvidenceFilters)
        event = get_object_or_404(Event.objects.public(), pk=id)
        queryset = event.evidence.order_by("id")
        count = queryset.count()
        offset, limit = values["offset"], values["limit"]
        return Response(
            {
                "items": EvidenceSerializer(queryset[offset : offset + limit], many=True).data,
                "total_count": count,
                "has_next": offset + limit < count,
            }
        )


class MapPointsView(PublicView):
    @extend_schema(
        parameters=[Filters],
        responses={200: MapResultSerializer, **ERRORS},
        operation_id="list_map_points",
    )
    def get(self, request):
        queryset = filtered_events(parameters(request, Filters)).exclude(location=None)
        count = queryset.count()
        points = [
            {
                "id": str(event.id),
                "longitude": event.location.x,
                "latitude": event.location.y,
                "kind": event.kind,
            }
            for event in queryset.only("id", "location", "kind", "occurred_on")[:2000]
        ]
        return Response({"points": points, "located_count": count, "truncated": count > 2000})
