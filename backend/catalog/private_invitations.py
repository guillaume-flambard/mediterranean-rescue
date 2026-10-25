"""The private API of invitations by single-use link (ADR 0015).

`invitations/` lists recent invitations and creates one (coordinators); the token comes back
once, in the creation response. `invitations/check/` reads what an invitation offers and
`invitations/accept/` spends it and signs the person in: both take the token in the body, never
in the address, and both are open to visitors, CSRF-checked and rate limited like sign-in.
"""

from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import exceptions, serializers
from rest_framework.permissions import AllowAny, BasePermission
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from .api import parameters
from .invitations import (
    INVITE_PERMISSION,
    ROLE_KEYS,
    InvitationRefused,
    accept_invitation,
    assignable_roles,
    create_invitation,
    revoke_invitation,
    usable,
)
from .models import Invitation
from .private_api import (
    ERRORS,
    Conflict,
    MeSerializer,
    PrivateSessionAuthentication,
    PrivateView,
    me_payload,
)


class CanInvite(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.has_perm(INVITE_PERMISSION))


class Refused(Conflict):
    default_code = "invitation_unusable"


def refused(exc):
    error = Refused(detail=" ".join(exc.messages))
    error.default_code = exc.code
    return error


class RoleSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    key = serializers.ChoiceField(choices=sorted(set(ROLE_KEYS.values())))


class InvitationSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    email = serializers.EmailField()
    roles = serializers.ListField(child=serializers.CharField())
    invited_by = serializers.CharField()
    created_at = serializers.DateTimeField()
    expires_at = serializers.DateTimeField()
    status = serializers.ChoiceField(choices=["waiting", "used", "revoked", "expired"])
    used_by = serializers.CharField(allow_null=True)


class InvitationListSerializer(serializers.Serializer):
    items = InvitationSerializer(many=True)
    roles = RoleSerializer(many=True, help_text="Roles this coordinator may give.")


class InvitationCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    roles = serializers.ListField(child=serializers.IntegerField(), max_length=10)


class InvitationCreatedSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    token = serializers.CharField(help_text="Shown once; the link is /invite#<token>.")
    expires_at = serializers.DateTimeField()


class TokenSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=200)


class InvitationOfferSerializer(serializers.Serializer):
    invited_by = serializers.CharField()
    roles = serializers.ListField(child=serializers.CharField())
    expires_at = serializers.DateTimeField()


def role_keys(invitation):
    return sorted(
        ROLE_KEYS[group.name] for group in invitation.groups.all() if group.name in ROLE_KEYS
    )


def status(invitation, now):
    if invitation.used_at:
        return "used"
    if invitation.revoked_at:
        return "revoked"
    return "expired" if invitation.expires_at <= now else "waiting"


def item(invitation, now):
    return {
        "id": invitation.pk,
        "email": invitation.email,
        "roles": role_keys(invitation),
        "invited_by": invitation.created_by.get_username(),
        "created_at": invitation.created_at,
        "expires_at": invitation.expires_at,
        "status": status(invitation, now),
        "used_by": invitation.used_by.get_username() if invitation.used_by else None,
    }


class InvitationsView(PrivateView):
    permission_classes = [CanInvite]

    @extend_schema(
        responses={200: InvitationListSerializer, **ERRORS}, operation_id="private_list_invitations"
    )
    def get(self, request):
        from django.utils import timezone

        parameters(request, serializers.Serializer)
        now = timezone.now()
        invitations = Invitation.objects.select_related("created_by", "used_by").prefetch_related(
            "groups"
        )[:100]
        roles = [{"id": g.pk, "key": ROLE_KEYS[g.name]} for g in assignable_roles(request.user)]
        return Response(
            InvitationListSerializer(
                {"items": [item(i, now) for i in invitations], "roles": roles}
            ).data
        )

    @extend_schema(
        request=InvitationCreateSerializer,
        responses={201: InvitationCreatedSerializer, **ERRORS},
        operation_id="private_create_invitation",
    )
    def post(self, request):
        body = InvitationCreateSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        groups = list(Group.objects.filter(pk__in=body.validated_data["roles"]))
        if len(groups) != len(set(body.validated_data["roles"])):
            raise exceptions.ValidationError({"roles": "Unknown role."})
        try:
            invitation, token = create_invitation(
                actor=request.user, email=body.validated_data["email"], groups=groups
            )
        except DjangoPermissionDenied as exc:
            raise exceptions.PermissionDenied() from exc
        except InvitationRefused as exc:
            raise refused(exc) from exc
        return Response(
            InvitationCreatedSerializer(
                {"id": invitation.pk, "token": token, "expires_at": invitation.expires_at}
            ).data,
            status=201,
        )


class InvitationView(PrivateView):
    permission_classes = [CanInvite]

    @extend_schema(
        request=None, responses={204: None, **ERRORS}, operation_id="private_revoke_invitation"
    )
    def delete(self, request, id):
        revoke_invitation(actor=request.user, invitation=get_object_or_404(Invitation, pk=id))
        return Response(status=204)


class OpenInvitationView(PrivateView):
    """Open to visitors, CSRF-checked and rate limited like sign-in."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    # Their own bucket: an invitation page must not use up the password sign-in attempts.
    throttle_scope = "invitations"

    def token(self, request):
        PrivateSessionAuthentication().enforce_csrf(request)
        body = TokenSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        return body.validated_data["token"]


class InvitationCheckView(OpenInvitationView):
    @extend_schema(
        request=TokenSerializer,
        responses={200: InvitationOfferSerializer, **ERRORS},
        operation_id="private_check_invitation",
    )
    def post(self, request):
        invitation = usable(self.token(request))
        if invitation is None:
            raise Refused(detail="This invitation link cannot be used")
        return Response(
            InvitationOfferSerializer(
                {
                    "invited_by": invitation.created_by.get_username(),
                    "roles": role_keys(invitation),
                    "expires_at": invitation.expires_at,
                }
            ).data
        )


class InvitationAcceptView(OpenInvitationView):
    @extend_schema(
        request=TokenSerializer,
        responses={200: MeSerializer, **ERRORS},
        operation_id="private_accept_invitation",
    )
    def post(self, request):
        token = self.token(request)
        try:
            user = accept_invitation(request._request, token)
        except InvitationRefused as exc:
            raise refused(exc) from exc
        response = Response(me_payload(user))
        from rescue.middleware import LOCAL_AUTO_LOGIN_OFF

        response.delete_cookie(LOCAL_AUTO_LOGIN_OFF)
        return response
