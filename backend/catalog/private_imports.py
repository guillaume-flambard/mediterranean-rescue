"""Private import API (ADR 0010): diagnose an export without keeping it, then stage it through
`stage_snapshot`, which diagnoses the bytes again and never trusts the browser."""

from collections import Counter

from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import exceptions, serializers
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from .api import parameters
from .crosswalk import blocking_reason, diagnose_for, propose_links, stage_snapshot
from .models import SHEETS, SheetSnapshot, Source
from .private_api import (
    ERRORS,
    REVIEW_SHEETS,
    STATUS_BY_PROPOSAL,
    STATUSES,
    CanStageOrReview,
    CanStageSnapshots,
    PageParams,
    PrivateView,
    QueueCountsSerializer,
    SourceRefSerializer,
)
from .sheets import load_contract

# Located anomalies returned by a diagnostic; the counts always cover all of them.
MAX_ISSUES = 200
BLOCKING_REASONS = ("read_rejected", "read_partial", "file_errors")
SEVERITIES = ("error", "warning")


class SourceOptionSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    key = serializers.CharField()
    name = serializers.CharField()
    synthetic = serializers.BooleanField()


class ImportOptionsSerializer(serializers.Serializer):
    sources = SourceOptionSerializer(many=True)
    sheets = serializers.ListField(child=serializers.ChoiceField(choices=SHEETS))
    max_bytes = serializers.IntegerField()


class ImportOptionsView(PrivateView):
    permission_classes = [CanStageSnapshots]

    @extend_schema(
        responses={200: ImportOptionsSerializer, **ERRORS}, operation_id="private_import_options"
    )
    def get(self, request):
        parameters(request, serializers.Serializer)
        contract = load_contract()
        return Response(
            ImportOptionsSerializer(
                {
                    "sources": Source.objects.order_by("name"),
                    "sheets": list(contract["sheets"]),
                    "max_bytes": contract["input"]["max_bytes"],
                }
            ).data
        )


class UploadSerializer(serializers.Serializer):
    source = serializers.UUIDField()
    sheet = serializers.ChoiceField(choices=SHEETS)
    file = serializers.FileField(allow_empty_file=True)

    def validate_source(self, value):
        source = Source.objects.filter(pk=value).first()
        if source is None:
            raise exceptions.ValidationError("Unknown source.")
        return source

    def validate_file(self, value):
        if value.size > load_contract()["input"]["max_bytes"]:
            raise exceptions.ValidationError("The file is larger than the accepted size.")
        return value


def read_upload(request):
    body = UploadSerializer(data=request.data)
    body.is_valid(raise_exception=True)
    values = body.validated_data
    return values["source"], values["sheet"], values["file"].read()


class CountsSerializer(serializers.Serializer):
    records_read = serializers.IntegerField()
    rows_diagnosed = serializers.IntegerField()
    blank_rows_skipped = serializers.IntegerField()
    file_errors = serializers.IntegerField()
    rows_with_errors = serializers.IntegerField()
    rows_with_warnings = serializers.IntegerField()
    errors = serializers.IntegerField()
    warnings = serializers.IntegerField()


class IssueCountSerializer(serializers.Serializer):
    code = serializers.CharField()
    severity = serializers.ChoiceField(choices=SEVERITIES)
    count = serializers.IntegerField()


class IssueSerializer(serializers.Serializer):
    severity = serializers.ChoiceField(choices=SEVERITIES)
    code = serializers.CharField()
    line = serializers.IntegerField(allow_null=True)
    column = serializers.IntegerField(allow_null=True)
    field = serializers.CharField(allow_null=True)


class DiagnosticSerializer(serializers.Serializer):
    source = SourceRefSerializer()
    sheet = serializers.ChoiceField(choices=SHEETS)
    sha256 = serializers.CharField()
    bytes = serializers.IntegerField()
    contract_version = serializers.CharField()
    source_read = serializers.CharField()
    normalization = serializers.CharField()
    counts = CountsSerializer()
    issues_by_code = IssueCountSerializer(many=True)
    issues = IssueSerializer(many=True)
    issues_truncated = serializers.BooleanField()
    stageable = serializers.BooleanField()
    blocking_reason = serializers.ChoiceField(choices=BLOCKING_REASONS, allow_null=True)
    existing_snapshot = serializers.UUIDField(allow_null=True)


def diagnostic_payload(source, sheet, result):
    by_code = Counter((issue["code"], issue["severity"]) for issue in result["issues"])
    existing = SheetSnapshot.objects.filter(
        source=source,
        sheet=sheet,
        sha256=result["snapshot"]["sha256"],
        contract_version=result["contract"]["version"],
    ).first()
    blocking = blocking_reason(result)
    counts = {key: result["counts"][key] for key in CountsSerializer().fields}
    return {
        "source": {"key": source.key, "name": source.name},
        "sheet": sheet,
        "sha256": result["snapshot"]["sha256"],
        "bytes": result["snapshot"]["bytes"],
        "contract_version": result["contract"]["version"],
        "source_read": result["status"]["source_read"],
        "normalization": result["status"]["normalization"],
        "counts": counts,
        "issues_by_code": [
            {"code": code, "severity": severity, "count": count}
            for (code, severity), count in sorted(by_code.items(), key=lambda item: -item[1])
        ],
        # Locations only: no source value leaves the server in a diagnostic.
        "issues": [
            {
                "severity": issue["severity"],
                "code": issue["code"],
                "line": issue.get("line"),
                "column": issue.get("column"),
                "field": issue.get("field"),
            }
            for issue in result["issues"][:MAX_ISSUES]
        ],
        "issues_truncated": len(result["issues"]) > MAX_ISSUES,
        "stageable": blocking is None,
        "blocking_reason": blocking,
        "existing_snapshot": existing.pk if existing else None,
    }


class ImportWriteView(PrivateView):
    permission_classes = [CanStageSnapshots]
    parser_classes = [MultiPartParser]
    throttle_scope = "imports"

    def get_throttles(self):
        return [ScopedRateThrottle()] if self.request.method == "POST" else []


class DiagnoseView(ImportWriteView):
    @extend_schema(
        request={"multipart/form-data": UploadSerializer},
        responses={200: DiagnosticSerializer, **ERRORS},
        operation_id="private_diagnose_import",
    )
    def post(self, request):
        source, sheet, content = read_upload(request)
        result = diagnose_for(source, sheet, content)
        return Response(DiagnosticSerializer(diagnostic_payload(source, sheet, result)).data)


class ErrorCountSerializer(serializers.Serializer):
    code = serializers.CharField()
    rows = serializers.IntegerField()


class ImportDetailSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    source = SourceRefSerializer()
    sheet = serializers.ChoiceField(choices=SHEETS)
    created_at = serializers.DateTimeField()
    staged_by = serializers.CharField()
    sha256 = serializers.CharField()
    byte_count = serializers.IntegerField()
    row_count = serializers.IntegerField()
    source_read = serializers.CharField()
    contract_version = serializers.CharField()
    rows_with_errors = serializers.IntegerField()
    errors_by_code = ErrorCountSerializer(many=True)
    review = QueueCountsSerializer(allow_null=True)


class ImportSummarySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    source = SourceRefSerializer()
    sheet = serializers.ChoiceField(choices=SHEETS)
    created_at = serializers.DateTimeField()
    staged_by = serializers.CharField()
    row_count = serializers.IntegerField()
    source_read = serializers.CharField()


class ImportPageSerializer(serializers.Serializer):
    items = ImportSummarySerializer(many=True)
    total_count = serializers.IntegerField()
    has_next = serializers.BooleanField()


class StagedSerializer(serializers.Serializer):
    created = serializers.BooleanField()
    snapshot = ImportDetailSerializer()


def summary_payload(snapshot):
    return {
        "id": snapshot.pk,
        "source": {"key": snapshot.source.key, "name": snapshot.source.name},
        "sheet": snapshot.sheet,
        "created_at": snapshot.created_at,
        "staged_by": snapshot.staged_by.get_username(),
        "row_count": snapshot.row_count,
        "source_read": snapshot.source_read,
    }


def detail_payload(snapshot):
    errors = Counter()
    rows_with_errors = 0
    for codes in snapshot.rows.values_list("error_codes", flat=True):
        rows_with_errors += bool(codes)
        errors.update(set(codes))
    review = None
    if snapshot.sheet in REVIEW_SHEETS:
        review = dict.fromkeys(STATUSES, 0)
        for proposal in propose_links(snapshot):
            review[STATUS_BY_PROPOSAL[proposal.kind]] += 1
    return {
        **summary_payload(snapshot),
        "sha256": snapshot.sha256,
        "byte_count": snapshot.byte_count,
        "contract_version": snapshot.contract_version,
        "rows_with_errors": rows_with_errors,
        "errors_by_code": [{"code": code, "rows": count} for code, count in errors.most_common()],
        "review": review,
    }


def load_snapshot(pk):
    return get_object_or_404(SheetSnapshot.objects.select_related("source", "staged_by"), pk=pk)


class ImportsView(ImportWriteView):
    def get_permissions(self):
        # Reviewers may read the list; only stagers may add an export.
        return [CanStageOrReview()] if self.request.method == "GET" else super().get_permissions()

    @extend_schema(
        parameters=[PageParams],
        responses={200: ImportPageSerializer, **ERRORS},
        operation_id="private_list_imports",
    )
    def get(self, request):
        values = parameters(request, PageParams)
        queryset = SheetSnapshot.objects.select_related("source", "staged_by").order_by(
            "-created_at", "-pk"
        )
        total = queryset.count()
        offset, limit = values["offset"], values["limit"]
        items = [summary_payload(snapshot) for snapshot in queryset[offset : offset + limit]]
        return Response(
            ImportPageSerializer(
                {"items": items, "total_count": total, "has_next": offset + limit < total}
            ).data
        )

    @extend_schema(
        request={"multipart/form-data": UploadSerializer},
        responses={200: StagedSerializer, 201: StagedSerializer, **ERRORS},
        operation_id="private_stage_import",
    )
    def post(self, request):
        source, sheet, content = read_upload(request)
        try:
            snapshot, created = stage_snapshot(
                source=source, sheet=sheet, content=content, actor=request.user
            )
        except DjangoValidationError as exc:
            raise exceptions.ValidationError({"file": exc.messages}) from exc
        payload = {"created": created, "snapshot": detail_payload(load_snapshot(snapshot.pk))}
        return Response(StagedSerializer(payload).data, status=201 if created else 200)


class ImportDetailView(PrivateView):
    permission_classes = [CanStageOrReview]

    @extend_schema(
        responses={200: ImportDetailSerializer, **ERRORS}, operation_id="private_retrieve_import"
    )
    def get(self, request, id):
        parameters(request, serializers.Serializer)
        return Response(ImportDetailSerializer(detail_payload(load_snapshot(id))).data)
