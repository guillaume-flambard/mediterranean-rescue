"""Private port reading API (ADR 0010). A label is the exact text of a source: a disembarkation
port of the latest Data_operations export or a name of the latest Data_ports export. Reading it
goes through `approve_port_alias` or `classify_port_label`; nothing is linked automatically."""

import hashlib
import hmac
from dataclasses import dataclass, field

from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from drf_spectacular.utils import extend_schema
from rest_framework import exceptions, serializers
from rest_framework.response import Response

from .api import parameters
from .crosswalk import (
    _port_name_index,
    _suggest,
    approve_port_alias,
    classify_port_label,
)
from .models import Port, PortAlias, SheetRow, SheetSnapshot, Source, Vessel
from .private_api import ERRORS, Conflict, PageParams, PrivateView, ReceivedSerializer, page

LABEL_STATUSES = ("to_read", "read")
INTERPRETATIONS = ("port", "ports", "vessel", "not_a_port")
MAX_OPERATION_LINES = 10


def label_id(source_id, label):
    # Keyed, so a port name cannot be recovered from an address by hashing known names.
    message = f"{source_id}\n{label}".encode()
    key = f"port-label:{settings.SECRET_KEY}".encode()
    return hmac.new(key, message, hashlib.sha256).hexdigest()[:32]


@dataclass
class LabelInfo:
    source: Source
    label: str
    operations: int = 0
    operation_lines: list = field(default_factory=list)
    port_list_row: SheetRow | None = None
    alias: PortAlias | None = None

    @property
    def id(self):
        return label_id(self.source.pk, self.label)


def latest_snapshot(source, sheet):
    return SheetSnapshot.objects.filter(source=source, sheet=sheet).order_by("-created_at").first()


def collect_labels():
    """Every label of every source, read or not. Counts come from the latest exports only."""
    labels = {}

    def info(source, label):
        key = (source.pk, label)
        if key not in labels:
            labels[key] = LabelInfo(source, label)
        return labels[key]

    for source in Source.objects.order_by("name"):
        operations = latest_snapshot(source, "Data_operations")
        if operations is not None:
            for row in operations.rows.order_by("line").only("id", "line", "candidate"):
                label = (row.candidate or {}).get("Port_disembarkation")
                if label:
                    entry = info(source, label)
                    entry.operations += 1
                    if len(entry.operation_lines) < MAX_OPERATION_LINES:
                        entry.operation_lines.append(
                            {"line": row.line, "occurred_on": row.candidate.get("occurred_on")}
                        )
        ports = latest_snapshot(source, "Data_ports")
        if ports is not None:
            for row in ports.rows.select_related("snapshot").order_by("line"):
                label = (row.candidate or {}).get("nom")
                if label and info(source, label).port_list_row is None:
                    info(source, label).port_list_row = row
        aliases = PortAlias.objects.filter(source=source).select_related("vessel", "approved_by")
        for alias in aliases.prefetch_related("ports"):
            info(source, alias.label).alias = alias
    return list(labels.values())


def find_label(id):
    for entry in collect_labels():
        if entry.id == id:
            return entry
    raise Http404


class PortPositionSerializer(serializers.Serializer):
    longitude = serializers.FloatField()
    latitude = serializers.FloatField()


class PortRefSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    country_code = serializers.CharField(allow_blank=True)
    position = PortPositionSerializer(allow_null=True)
    location_source = serializers.CharField(allow_blank=True)


class VesselRefSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    imo = serializers.CharField(allow_blank=True)


class PortListRowSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    line = serializers.IntegerField()
    position = PortPositionSerializer(allow_null=True)
    error_codes = serializers.ListField(child=serializers.CharField())


class ReadingSerializer(serializers.Serializer):
    interpretation = serializers.ChoiceField(choices=INTERPRETATIONS)
    ports = PortRefSerializer(many=True)
    vessel = VesselRefSerializer(allow_null=True)
    approved_by = serializers.CharField()
    approved_at = serializers.DateTimeField()
    reason = serializers.CharField()


class LabelSourceSerializer(serializers.Serializer):
    key = serializers.CharField()
    name = serializers.CharField()


class LabelSerializer(serializers.Serializer):
    id = serializers.CharField()
    label = serializers.CharField()
    source = LabelSourceSerializer()
    status = serializers.ChoiceField(choices=LABEL_STATUSES)
    operations = serializers.IntegerField()
    port_list_row = PortListRowSerializer(allow_null=True)
    suggested_port = PortRefSerializer(allow_null=True)
    reading = ReadingSerializer(allow_null=True)


class OperationLineSerializer(serializers.Serializer):
    line = serializers.IntegerField()
    occurred_on = serializers.CharField(allow_null=True)


class LabelDetailSerializer(LabelSerializer):
    port_list_cells = ReceivedSerializer(allow_null=True)
    operation_lines = OperationLineSerializer(many=True)


class LabelCountsSerializer(serializers.Serializer):
    to_read = serializers.IntegerField()
    read = serializers.IntegerField()


class LabelPageSerializer(serializers.Serializer):
    items = LabelSerializer(many=True)
    total_count = serializers.IntegerField()
    has_next = serializers.BooleanField()
    counts = LabelCountsSerializer()


def port_ref(port):
    return {
        "id": port.pk,
        "name": port.name,
        "country_code": port.country_code,
        "position": None
        if port.location is None
        else {"longitude": port.location.x, "latitude": port.location.y},
        "location_source": port.location_source,
    }


def row_position(row):
    position = (row.candidate or {}).get("position")
    if not position:
        return None
    longitude, latitude = float(position["longitude"]), float(position["latitude"])
    # 0,0 is only a warning in the diagnostic, but never a usable port position.
    if longitude == 0 and latitude == 0:
        return None
    return {"longitude": longitude, "latitude": latitude}


def reading_payload(alias):
    if alias is None:
        return None
    ports = sorted(alias.ports.all(), key=lambda port: port.name)
    interpretation = alias.target
    if alias.target == "ports":
        interpretation = "port" if len(ports) == 1 else "ports"
    return {
        "interpretation": interpretation,
        "ports": [port_ref(port) for port in ports],
        "vessel": None
        if alias.vessel is None
        else {"id": alias.vessel.pk, "name": alias.vessel.name, "imo": alias.vessel.imo},
        "approved_by": alias.approved_by.get_username(),
        "approved_at": alias.created_at,
        "reason": alias.reason,
    }


def label_payload(entry, index, ports_by_id):
    row = entry.port_list_row
    suggested = None if entry.alias else _suggest(index, entry.label)
    return {
        "id": entry.id,
        "label": entry.label,
        "source": {"key": entry.source.key, "name": entry.source.name},
        "status": "read" if entry.alias else "to_read",
        "operations": entry.operations,
        "port_list_row": None
        if row is None
        else {
            "id": row.pk,
            "line": row.line,
            "position": row_position(row),
            "error_codes": row.error_codes,
        },
        "suggested_port": port_ref(ports_by_id[suggested]) if suggested else None,
        "reading": reading_payload(entry.alias),
    }


def detail_payload(entry):
    index = _port_name_index()
    suggested = _suggest(index, entry.label)
    ports_by_id = Port.objects.in_bulk([suggested] if suggested else [])
    row = entry.port_list_row
    return {
        **label_payload(entry, index, ports_by_id),
        "port_list_cells": None
        if row is None
        else {"headers": row.snapshot.header_cells, "cells": row.raw_cells},
        "operation_lines": entry.operation_lines,
    }


class LabelParams(PageParams):
    status = serializers.ChoiceField(choices=LABEL_STATUSES, default="to_read")


class PortLabelsView(PrivateView):
    @extend_schema(
        parameters=[LabelParams],
        responses={200: LabelPageSerializer, **ERRORS},
        operation_id="private_list_port_labels",
    )
    def get(self, request):
        values = parameters(request, LabelParams)
        entries = collect_labels()
        counts = {
            "to_read": sum(entry.alias is None for entry in entries),
            "read": sum(entry.alias is not None for entry in entries),
        }
        if values["status"] == "to_read":
            selected = sorted(
                (entry for entry in entries if entry.alias is None),
                key=lambda entry: (-entry.operations, entry.label.casefold()),
            )
        else:
            selected = sorted(
                (entry for entry in entries if entry.alias is not None),
                key=lambda entry: entry.alias.created_at,
                reverse=True,
            )
        index = _port_name_index()
        window = page(values, selected)
        suggested = [_suggest(index, entry.label) for entry in window["items"]]
        ports_by_id = Port.objects.in_bulk([pk for pk in suggested if pk])
        window["items"] = [label_payload(entry, index, ports_by_id) for entry in window["items"]]
        return Response(LabelPageSerializer({**window, "counts": counts}).data)


class PortLabelView(PrivateView):
    @extend_schema(
        responses={200: LabelDetailSerializer, **ERRORS},
        operation_id="private_retrieve_port_label",
    )
    def get(self, request, id):
        parameters(request, serializers.Serializer)
        return Response(LabelDetailSerializer(detail_payload(find_label(id))).data)


class NewPortSerializer(serializers.Serializer):
    from_port_list = serializers.BooleanField(default=False)
    longitude = serializers.FloatField(required=False, min_value=-180, max_value=180)
    latitude = serializers.FloatField(required=False, min_value=-90, max_value=90)
    country_code = serializers.RegexField(r"^[A-Z]{2}$", allow_blank=True, default="")

    def validate(self, attrs):
        given = [key for key in ("longitude", "latitude") if key in attrs]
        if len(given) == 1:
            raise exceptions.ValidationError("Give both longitude and latitude.")
        if given and attrs["longitude"] == 0 and attrs["latitude"] == 0:
            raise exceptions.ValidationError("0,0 is not accepted as a port position.")
        if not given and not attrs["from_port_list"]:
            raise exceptions.ValidationError(
                "A new port needs its position, or the row of the port list."
            )
        return attrs


class LabelDecisionSerializer(serializers.Serializer):
    interpretation = serializers.ChoiceField(choices=INTERPRETATIONS)
    ports = serializers.ListField(
        child=serializers.UUIDField(), required=False, max_length=6, default=list
    )
    new_port = NewPortSerializer(required=False)
    vessel = serializers.UUIDField(required=False)
    reason = serializers.CharField(max_length=2000)

    def validate(self, attrs):
        kind, ports = attrs["interpretation"], attrs["ports"]
        new_port, vessel = attrs.get("new_port"), attrs.get("vessel")
        if len(set(ports)) != len(ports):
            raise exceptions.ValidationError({"ports": "A port is listed twice."})
        if kind == "port" and (len(ports) + bool(new_port)) != 1:
            raise exceptions.ValidationError({"ports": "Choose one port, existing or new."})
        if kind == "ports" and (len(ports) < 2 or new_port):
            raise exceptions.ValidationError({"ports": "Choose at least two existing ports."})
        if kind == "vessel" and (vessel is None or ports or new_port):
            raise exceptions.ValidationError({"vessel": "Choose the ship."})
        if kind == "not_a_port" and (ports or new_port or vessel):
            raise exceptions.ValidationError(
                {"interpretation": "Not a port takes no port or ship."}
            )
        if kind in ("port", "ports") and vessel is not None:
            raise exceptions.ValidationError({"vessel": "A port reading takes no ship."})
        return attrs


class PortLabelDecisionView(PrivateView):
    @extend_schema(
        request=LabelDecisionSerializer,
        responses={200: LabelDetailSerializer, **ERRORS},
        operation_id="private_decide_port_label",
    )
    def post(self, request, id):
        body = LabelDecisionSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        values = body.validated_data
        entry = find_label(id)
        if entry.alias is not None:
            raise Conflict(detail="This name already has a reading; reload it.")
        if len(entry.label) > PortAlias._meta.get_field("label").max_length:
            raise exceptions.ValidationError(
                {"interpretation": "This name is too long to be read; fix it in the source."}
            )
        common = {
            "source": entry.source,
            "label": entry.label,
            "actor": request.user,
            "reason": values["reason"],
        }
        kind = values["interpretation"]
        try:
            if kind in ("port", "ports") and values["ports"]:
                ports = list(Port.objects.filter(pk__in=values["ports"]))
                if len(ports) != len(values["ports"]):
                    raise exceptions.ValidationError({"ports": "Unknown port."})
                approve_port_alias(**common, ports=ports)
            elif kind == "port":
                approve_port_alias(**common, **self.new_port(entry, values["new_port"]))
            elif kind == "vessel":
                vessel = Vessel.objects.filter(pk=values["vessel"]).first()
                if vessel is None:
                    raise exceptions.ValidationError({"vessel": "Unknown ship."})
                classify_port_label(**common, vessel=vessel)
            else:
                classify_port_label(**common)
        except DjangoValidationError as exc:
            message = " ".join(exc.messages)
            # Only a reading recorded meanwhile is a conflict; other refusals are input errors.
            if "approved reading" in message or "Concurrent reading" in message:
                raise Conflict(detail=message) from exc
            raise exceptions.ValidationError({"new_port": exc.messages}) from exc
        return Response(LabelDetailSerializer(detail_payload(find_label(id))).data)

    @staticmethod
    def new_port(entry, values):
        row = entry.port_list_row if values["from_port_list"] else None
        if values["from_port_list"] and row is None:
            raise exceptions.ValidationError({"new_port": "This name is not in the port list."})
        location = None
        if "longitude" in values:
            location = Point(values["longitude"], values["latitude"], srid=4326)
        elif row is not None and (row.error_codes or row_position(row) is None):
            raise exceptions.ValidationError(
                {"new_port": "The port list gives no usable position; enter it."}
            )
        return {"row": row, "location": location, "country_code": values["country_code"]}


class PortSearchParams(serializers.Serializer):
    q = serializers.CharField(required=False, max_length=100)
    limit = serializers.IntegerField(min_value=1, max_value=50, default=20)


class PortSearchSerializer(serializers.Serializer):
    items = PortRefSerializer(many=True)


class PortsView(PrivateView):
    @extend_schema(
        parameters=[PortSearchParams],
        responses={200: PortSearchSerializer, **ERRORS},
        operation_id="private_search_ports",
    )
    def get(self, request):
        values = parameters(request, PortSearchParams)
        queryset = Port.objects.order_by("name", "pk")
        if query := values.get("q", "").strip():
            queryset = queryset.filter(name__icontains=query)
        items = [port_ref(port) for port in queryset[: values["limit"]]]
        return Response(PortSearchSerializer({"items": items}).data)


class VesselListSerializer(serializers.Serializer):
    items = VesselRefSerializer(many=True)


class VesselsView(PrivateView):
    @extend_schema(
        responses={200: VesselListSerializer, **ERRORS}, operation_id="private_list_vessels"
    )
    def get(self, request):
        parameters(request, serializers.Serializer)
        vessels = Vessel.objects.order_by("name", "pk")[:200]
        items = [{"id": v.pk, "name": v.name, "imo": v.imo} for v in vessels]
        return Response(VesselListSerializer({"items": items}).data)
