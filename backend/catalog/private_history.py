"""The team's decisions, newest first: who decided what, when, and why.

`GET history/?scope=mine|team&kind=…` gathers the decisions the models already record with their
author, date and reason: verifications (RowIdentityLink), preparations (SourceIdentity drafts),
publications and withdrawals (PublicationAudit), port name readings (PortAlias) and corrections
(EventRevision). Nothing new is stored; this only reads. Any team member may read the team's
history: decisions are shared work, and every one of them already names its author.
"""

from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from .api import parameters
from .models import EventRevision, PortAlias, PublicationAudit, RowIdentityLink, SourceIdentity
from .private_api import ERRORS, REVIEW_PERMISSION, STAGE_PERMISSION, PageParams, PrivateView

KINDS = ("verify", "prepare", "publish", "withdraw", "port", "correction")
TEAM_PERMISSIONS = (
    REVIEW_PERMISSION,
    STAGE_PERMISSION,
    "catalog.add_event",
    "catalog.publish_event",
    "catalog.add_invitation",
)


class AnyTeamRole(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and any(user.has_perm(p) for p in TEAM_PERMISSIONS)
        )


class HistoryParams(PageParams):
    scope = serializers.ChoiceField(choices=["mine", "team"], default="mine")
    kind = serializers.ChoiceField(choices=KINDS, required=False)


class HistorySubjectSerializer(serializers.Serializer):
    occurred_on = serializers.CharField(allow_null=True)
    kind = serializers.CharField(allow_null=True)
    people = serializers.IntegerField(allow_null=True)
    label = serializers.CharField(allow_null=True, help_text="Port name, for a port reading.")


class HistoryItemSerializer(serializers.Serializer):
    id = serializers.CharField()
    kind = serializers.ChoiceField(choices=KINDS)
    at = serializers.DateTimeField()
    actor = serializers.CharField()
    reason = serializers.CharField()
    detail = serializers.CharField(
        allow_blank=True, help_text="new, reviewed_match, applied, ports, vessel…"
    )
    subject = HistorySubjectSerializer()
    path = serializers.CharField(allow_null=True, help_text="Where the decided item can be seen.")


class HistoryPageSerializer(serializers.Serializer):
    items = HistoryItemSerializer(many=True)
    has_next = serializers.BooleanField()


def _subject(candidate=None, label=None):
    candidate = candidate or {}
    return {
        "occurred_on": candidate.get("occurred_on"),
        "kind": candidate.get("kind"),
        "people": candidate.get("nb_survivor", candidate.get("people")),
        "label": label,
    }


def _verifications(actor, limit):
    links = RowIdentityLink.objects.select_related("approved_by", "row").order_by("-created_at")
    if actor is not None:
        links = links.filter(approved_by=actor)
    for link in links[:limit]:
        yield {
            "id": f"verify:{link.pk}",
            "kind": "verify",
            "at": link.created_at,
            "actor": link.approved_by.get_username(),
            "reason": link.reason,
            "detail": link.match,
            "subject": _subject(link.row.candidate),
            "path": f"/workspace/review/{link.snapshot_id}/rows/{link.row_id}",
        }


def _preparations(actor, limit):
    identities = (
        SourceIdentity.objects.exclude(drafted_at=None)
        .select_related("drafted_by", "drafted_from", "event")
        .order_by("-drafted_at")
    )
    if actor is not None:
        identities = identities.filter(drafted_by=actor)
    for identity in identities[:limit]:
        event = identity.event
        yield {
            "id": f"prepare:{identity.pk}",
            "kind": "prepare",
            "at": identity.drafted_at,
            "actor": identity.drafted_by.get_username() if identity.drafted_by else "",
            "reason": identity.draft_reason,
            "detail": "",
            "subject": _subject(
                {
                    "occurred_on": str(event.occurred_on) if event else None,
                    "kind": event.kind if event else None,
                    "people": event.people if event else None,
                }
            ),
            "path": "/workspace/publish",
        }


def _publications(actor, limit, actions):
    audits = (
        PublicationAudit.objects.filter(action__in=actions)
        .select_related("actor", "event")
        .order_by("-created_at")
    )
    if actor is not None:
        audits = audits.filter(actor=actor)
    for audit in audits[:limit]:
        decided = dict(audit.snapshot or {})
        decided.setdefault("kind", audit.event.kind)
        yield {
            "id": f"publication:{audit.pk}",
            "kind": "publish" if audit.action == "published" else "withdraw",
            "at": audit.created_at,
            "actor": audit.actor.get_username(),
            "reason": audit.reason,
            "detail": audit.action,
            "subject": _subject(decided),
            "path": "/workspace/publish",
        }


def _ports(actor, limit):
    aliases = PortAlias.objects.select_related("approved_by").order_by("-created_at")
    if actor is not None:
        aliases = aliases.filter(approved_by=actor)
    for alias in aliases[:limit]:
        yield {
            "id": f"port:{alias.pk}",
            "kind": "port",
            "at": alias.created_at,
            "actor": alias.approved_by.get_username(),
            "reason": alias.reason,
            "detail": alias.target,
            "subject": _subject(label=alias.label),
            "path": "/workspace/ports",
        }


def _corrections(actor, limit):
    revisions = EventRevision.objects.select_related("decided_by", "event").order_by("-created_at")
    if actor is not None:
        revisions = revisions.filter(decided_by=actor)
    for revision in revisions[:limit]:
        event = revision.event
        yield {
            "id": f"correction:{revision.pk}",
            "kind": "correction",
            "at": revision.created_at,
            "actor": revision.decided_by.get_username(),
            "reason": revision.reason,
            "detail": revision.decision,
            "subject": _subject(
                {"occurred_on": str(event.occurred_on), "kind": event.kind, "people": event.people}
            ),
            "path": "/workspace/publish",
        }


def history(actor, kind, limit):
    """The newest `limit` decisions of every kind, merged by date (actor None: the whole team)."""
    sources = {
        "verify": lambda: _verifications(actor, limit),
        "prepare": lambda: _preparations(actor, limit),
        "publish": lambda: _publications(actor, limit, ["published"]),
        "withdraw": lambda: _publications(actor, limit, ["withdrawn"]),
        "port": lambda: _ports(actor, limit),
        "correction": lambda: _corrections(actor, limit),
    }
    chosen = [sources[kind]] if kind else list(sources.values())
    items = [item for source in chosen for item in source()]
    return sorted(items, key=lambda item: item["at"], reverse=True)[:limit]


class HistoryView(PrivateView):
    permission_classes = [AnyTeamRole]

    @extend_schema(
        parameters=[HistoryParams],
        responses={200: HistoryPageSerializer, **ERRORS},
        operation_id="private_history",
    )
    def get(self, request):
        values = parameters(request, HistoryParams)
        offset, limit = values["offset"], values["limit"]
        actor = request.user if values["scope"] == "mine" else None
        # One more than the page, to know whether another page exists.
        items = history(actor, values.get("kind"), offset + limit + 1)
        return Response(
            HistoryPageSerializer(
                {"items": items[offset : offset + limit], "has_next": len(items) > offset + limit}
            ).data
        )
