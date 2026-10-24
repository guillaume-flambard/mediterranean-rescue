"""Private publication API (ADR 0013). The team space takes a verified event to the public site in
two steps, each a named human decision with a reason: prepare (drafts from the verified rows of the
latest exports, through `drafts.create_drafts`) and publish or withdraw (through
`services.set_publication`, which checks the permission, the source's publication rights and
records the audit). Nothing here bypasses those services."""

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import exceptions, serializers
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from .api import parameters
from .crosswalk import REVIEW_PERMISSION
from .drafts import DRAFT_PERMISSION, EVENT_SHEETS, create_drafts, plan_drafts
from .models import Event, EventKind, SheetSnapshot, Source
from .private_api import ERRORS, Conflict, PageParams, PrivateView, has_any_perm
from .services import set_publication

PUBLISH_PERMISSION = "catalog.publish_event"
EVENT_STATUSES = ("draft", "published", "withdrawn")
# Plan outcomes as the team space groups them: ready to prepare, already prepared, changed in the
# sheet since it was prepared, waiting for verification, and needing a fix before it can be used.
OUTCOME_GROUPS = {
    "ready": "ready",
    "already_drafted": "prepared",
    "revision_needed": "changed",
    "revision_rejected": "prepared",
    "not_linked": "not_verified",
    "position_to_review": "to_fix",
    "inconsistent_counts": "to_fix",
    "invalid_draft": "to_fix",
    "row_already_drafted": "to_fix",
}
GROUPS = ("ready", "prepared", "changed", "not_verified", "to_fix")
MAX_DECISIONS = 100
PUBLICATION_ACTIONS = ("publish", "withdraw")


class RightsNotApproved(Conflict):
    default_code = "rights_not_approved"
    default_detail = "The source's publication rights are not recorded yet; nothing was published."


class CanFollowPublication(BasePermission):
    def has_permission(self, request, view):
        return has_any_perm(request.user, REVIEW_PERMISSION, DRAFT_PERMISSION, PUBLISH_PERMISSION)


def latest_event_snapshots():
    """The latest export of each event sheet, per source."""
    latest = {}
    for snapshot in (
        SheetSnapshot.objects.filter(sheet__in=EVENT_SHEETS)
        .select_related("source")
        .order_by("-created_at", "-pk")
    ):
        latest.setdefault((snapshot.source_id, snapshot.sheet), snapshot)
    return list(latest.values())


# Overview


class SourceRightsSerializer(serializers.Serializer):
    name = serializers.CharField()
    rights_approved = serializers.BooleanField()


class PreparationSerializer(serializers.Serializer):
    sheet = serializers.CharField()
    exported_at = serializers.DateTimeField()
    ready = serializers.IntegerField()
    prepared = serializers.IntegerField()
    changed = serializers.IntegerField()
    not_verified = serializers.IntegerField()
    to_fix = serializers.IntegerField()


class EventCountsSerializer(serializers.Serializer):
    draft = serializers.IntegerField()
    published = serializers.IntegerField()
    withdrawn = serializers.IntegerField()


class PublicationAbilitiesSerializer(serializers.Serializer):
    prepare = serializers.BooleanField()
    publish = serializers.BooleanField()


class PublicationOverviewSerializer(serializers.Serializer):
    sources = SourceRightsSerializer(many=True)
    preparation = PreparationSerializer(many=True)
    events = EventCountsSerializer()
    can = PublicationAbilitiesSerializer()


def overview_payload(user):
    preparation = []
    for snapshot in latest_event_snapshots():
        counts = dict.fromkeys(GROUPS, 0)
        for plan in plan_drafts(snapshot):
            group = OUTCOME_GROUPS.get(plan.outcome)
            if group:
                counts[group] += 1
        preparation.append({"sheet": snapshot.sheet, "exported_at": snapshot.created_at, **counts})
    preparation.sort(key=lambda item: item["sheet"])
    events = dict.fromkeys(EVENT_STATUSES, 0)
    for status in Event.objects.values_list("status", flat=True):
        events[status] += 1
    source_ids = {snapshot.source_id for snapshot in latest_event_snapshots()} | set(
        Event.objects.values_list("source_id", flat=True).distinct()
    )
    sources = [
        {"name": source.name, "rights_approved": source.rights_approved}
        for source in Source.objects.filter(pk__in=source_ids).order_by("name")
    ]
    return {
        "sources": sources,
        "preparation": preparation,
        "events": events,
        "can": {
            "prepare": user.has_perm(DRAFT_PERMISSION),
            "publish": user.has_perm(PUBLISH_PERMISSION),
        },
    }


class PublicationOverviewView(PrivateView):
    permission_classes = [CanFollowPublication]

    @extend_schema(
        responses={200: PublicationOverviewSerializer, **ERRORS},
        operation_id="private_publication_overview",
    )
    def get(self, request):
        parameters(request, serializers.Serializer)
        return Response(PublicationOverviewSerializer(overview_payload(request.user)).data)


# Prepare


class ReasonSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500, trim_whitespace=True)


class PreparedSerializer(serializers.Serializer):
    created = serializers.IntegerField()
    overview = PublicationOverviewSerializer()


class PrepareView(PrivateView):
    permission_classes = [CanFollowPublication]

    @extend_schema(
        request=ReasonSerializer,
        responses={200: PreparedSerializer, **ERRORS},
        operation_id="private_prepare_drafts",
    )
    def post(self, request):
        body = ReasonSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        created = 0
        try:
            # Every sheet or none: a refusal on one export leaves the other untouched too.
            with transaction.atomic():
                for snapshot in latest_event_snapshots():
                    result = create_drafts(
                        snapshot=snapshot, actor=request.user, reason=body.validated_data["reason"]
                    )
                    created += len(result.created)
        except DjangoPermissionDenied as exc:
            raise exceptions.PermissionDenied() from exc
        except DjangoValidationError as exc:
            raise Conflict(detail=" ".join(exc.messages)) from exc
        payload = {"created": created, "overview": overview_payload(request.user)}
        return Response(PreparedSerializer(payload).data)


# Events and decisions


class PublicationEventsParams(PageParams):
    status = serializers.ChoiceField(choices=EVENT_STATUSES, default="draft")


class PublicationEventSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    kind = serializers.ChoiceField(choices=EventKind.choices)
    occurred_on = serializers.DateField()
    people = serializers.IntegerField(allow_null=True)
    port = serializers.CharField(allow_null=True)
    located = serializers.BooleanField()
    status = serializers.ChoiceField(choices=EVENT_STATUSES)
    published_at = serializers.DateTimeField(allow_null=True)
    source = serializers.CharField()
    rights_approved = serializers.BooleanField()


class PublicationEventsSerializer(serializers.Serializer):
    items = PublicationEventSerializer(many=True)
    total_count = serializers.IntegerField()
    has_next = serializers.BooleanField()


def event_payload(event):
    return {
        "id": event.pk,
        "kind": event.kind,
        "occurred_on": event.occurred_on,
        "people": event.people,
        "port": event.port.name if event.port_id else None,
        "located": event.location is not None,
        "status": event.status,
        "published_at": event.published_at,
        "source": event.source.name,
        "rights_approved": event.source.rights_approved,
    }


class PublicationEventsView(PrivateView):
    permission_classes = [CanFollowPublication]

    @extend_schema(
        parameters=[PublicationEventsParams],
        responses={200: PublicationEventsSerializer, **ERRORS},
        operation_id="private_publication_events",
    )
    def get(self, request):
        values = parameters(request, PublicationEventsParams)
        events = (
            Event.objects.filter(status=values["status"])
            .select_related("source", "port")
            .order_by("-occurred_on", "id")
        )
        total = events.count()
        offset, limit = values["offset"], values["limit"]
        items = [event_payload(event) for event in events[offset : offset + limit]]
        return Response(
            PublicationEventsSerializer(
                {"items": items, "total_count": total, "has_next": offset + limit < total}
            ).data
        )


class DecisionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=PUBLICATION_ACTIONS)
    events = serializers.ListField(
        child=serializers.UUIDField(), min_length=1, max_length=MAX_DECISIONS
    )
    reason = serializers.CharField(max_length=500, trim_whitespace=True)


class DecidedSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=PUBLICATION_ACTIONS)
    count = serializers.IntegerField()


class PublicationDecisionView(PrivateView):
    permission_classes = [CanFollowPublication]

    @extend_schema(
        request=DecisionSerializer,
        responses={200: DecidedSerializer, **ERRORS},
        operation_id="private_decide_publication",
    )
    def post(self, request):
        body = DecisionSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        values = body.validated_data
        publish = values["action"] == "publish"
        if not request.user.has_perm(PUBLISH_PERMISSION):
            raise exceptions.PermissionDenied()
        ids = list(dict.fromkeys(values["events"]))
        # Publishing takes a draft or a withdrawn event; withdrawing takes a published one.
        allowed = ("draft", "withdrawn") if publish else ("published",)
        try:
            # All or nothing: one refusal leaves every event as it was.
            with transaction.atomic():
                events = list(
                    Event.objects.select_for_update().filter(pk__in=ids).select_related("source")
                )
                if len(events) != len(ids):
                    raise exceptions.NotFound()
                if any(event.status not in allowed for event in events):
                    raise Conflict(detail="An event changed meanwhile; reload and decide again.")
                if publish and any(not event.source.rights_approved for event in events):
                    raise RightsNotApproved()
                for event in events:
                    set_publication(
                        event_id=event.pk,
                        actor=request.user,
                        publish=publish,
                        reason=values["reason"],
                    )
        except DjangoPermissionDenied as exc:
            raise exceptions.PermissionDenied() from exc
        except DjangoValidationError as exc:
            message = " ".join(exc.messages)
            if "rights" in message:
                raise RightsNotApproved() from exc
            raise Conflict(detail=message) from exc
        return Response(DecidedSerializer({"action": values["action"], "count": len(events)}).data)
