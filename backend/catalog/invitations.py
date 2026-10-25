"""Invitations by single-use link (ADR 0015).

A coordinator invites a volunteer by email with volunteer roles and copies the link it gets
back; nothing is emailed by the application. The link carries a random token (Python `secrets`,
32 bytes) after a `#`, so it never reaches a server log; only its SHA-256 is stored. Opening the
link only reads the invitation; joining is a separate POST, so a mail scanner that follows links
uses nothing up. A link works once, for 72 hours, and never signs in a staff or superuser
account: those keep their password.
"""

import hashlib
import re
import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model, login
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, connection, transaction
from django.utils import timezone

from .models import Invitation

INVITE_PERMISSION = "catalog.add_invitation"
TOKEN_TTL = timedelta(hours=72)
# Roles a coordinator may hand out; publishing and coordination stay with a superuser (ADR 0013).
RESTRICTED_ROLES = ("Coordinator", "Publish events")
ROLE_KEYS = {
    "Verify events": "verify",
    "Prepare events": "prepare",
    "Publish events": "publish",
    "Manual import": "import",
    "Coordinator": "coordinator",
}


class InvitationRefused(ValidationError):
    def __init__(self, code, message):
        super().__init__(message, code=code)


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def holds_admin(user):
    return user.is_staff or user.is_superuser


def may_invite(creator):
    return creator.is_active and creator.has_perm(INVITE_PERMISSION)


def may_be_signed_in_by_link(user, creator):
    """Whether a link from this creator may open this existing account.

    Never an admin or inactive account. An account that may publish or coordinate (by role or
    individual permission) only by a superuser's link: otherwise a coordinator could open a
    publisher's session, which the admin forbids (security review of 25 October 2026)."""
    if holds_admin(user) or not user.is_active:
        return False
    # Opening an existing account is the admin's password-reset power: staff coordinators only.
    if not (creator.is_staff or creator.is_superuser):
        return False
    sensitive = user.groups.filter(name__in=RESTRICTED_ROLES).exists() or user.has_perm(
        "catalog.publish_event"
    )
    return creator.is_superuser or not sensitive


def assignable_roles(actor):
    groups = Group.objects.filter(name__in=ROLE_KEYS).order_by("name")
    return groups if actor.is_superuser else groups.exclude(name__in=RESTRICTED_ROLES)


def _accounts(email):
    return get_user_model().objects.filter(email__iexact=email)


@transaction.atomic
def create_invitation(*, actor, email, groups):
    """Returns (invitation, token). The token is not stored and cannot be shown again.

    The answer is the same whatever account the address belongs to, so a coordinator learns
    nothing about admin accounts; a link that may not open the account is refused when used."""
    if not may_invite(actor):
        raise PermissionDenied("Inviting needs the coordinator role")
    email = email.strip().lower()
    allowed = set(assignable_roles(actor).values_list("pk", flat=True))
    if any(group.pk not in allowed for group in groups):
        raise InvitationRefused("role_not_allowed", "Only a superuser gives these roles")
    accounts = list(_accounts(email)[:2])
    token = secrets.token_urlsafe(32)
    invitation = Invitation.objects.create(
        email=email,
        token_hash=token_hash(token),
        created_by=actor,
        expires_at=timezone.now() + TOKEN_TTL,
        user=accounts[0] if len(accounts) == 1 else None,
    )
    invitation.groups.set(groups)
    return invitation, token


def _is_open(invitation):
    return (
        invitation.used_at is None
        and invitation.revoked_at is None
        and invitation.expires_at > timezone.now()
    )


def usable(token):
    """The invitation a token opens, or None: unknown, used, revoked and expired look the same."""
    if not isinstance(token, str) or not 20 <= len(token) <= 200:
        return None
    invitation = (
        Invitation.objects.filter(token_hash=token_hash(token)).select_related("created_by").first()
    )
    if invitation is None or not _is_open(invitation) or not may_invite(invitation.created_by):
        return None
    return invitation


def _new_username(email):
    base = re.sub(r"[^a-z0-9._-]", "", email.split("@")[0].lower())[:30] or "volunteer"
    users = get_user_model().objects
    name, number = base, 1
    while users.filter(username=name).exists():
        number += 1
        name = f"{base}{number}"
    return name


def _create_account(email):
    users = get_user_model().objects
    for _ in range(5):
        try:
            with transaction.atomic():
                user = users.create_user(username=_new_username(email), email=email)
                user.set_unusable_password()
                user.save()
                return user
        except IntegrityError:
            continue  # the same username taken meanwhile by another sign-up
    raise UNUSABLE


UNUSABLE = InvitationRefused("invitation_unusable", "This invitation link cannot be used")


@transaction.atomic
def accept_invitation(request, token):
    """Signs the invited person in (creating their account the first time) and spends the link."""
    found = usable(token)
    if found is None:
        raise UNUSABLE
    # One acceptance per address at a time: two links to one new address never make two accounts.
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", [found.email.lower()])
    invitation = (
        Invitation.objects.select_for_update().select_related("created_by").get(pk=found.pk)
    )
    creator = invitation.created_by
    if not _is_open(invitation) or not may_invite(creator):
        raise UNUSABLE
    accounts = list(_accounts(invitation.email)[:2])
    if invitation.user_id is not None:
        # The account it was made for, still holding that address, and still one a link may open.
        user = invitation.user
        if len(accounts) != 1 or accounts[0].pk != user.pk:
            raise UNUSABLE
        if not may_be_signed_in_by_link(user, creator):
            raise UNUSABLE
    elif accounts:
        # An account took this address after the link was made: never open it.
        raise UNUSABLE
    else:
        user = _create_account(invitation.email)
    user.groups.add(*invitation.groups.all())
    invitation.used_at = timezone.now()
    invitation.used_by = user
    invitation.save(update_fields=["used_at", "used_by", "updated_at"])
    # Rotates the session key and the CSRF token.
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return user


def revoke_invitation(*, actor, invitation):
    if not may_invite(actor):
        raise PermissionDenied("Revoking needs the coordinator role")
    if invitation.used_at is None and invitation.revoked_at is None:
        invitation.revoked_at = timezone.now()
        invitation.save(update_fields=["revoked_at", "updated_at"])
