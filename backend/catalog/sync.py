"""Scheduled reading of the Google Sheets exports (ADR 0012).

Every few minutes each configured tab is downloaded from its public CSV export. Identical bytes
are recorded as "unchanged"; new bytes go through `stage_snapshot`, which diagnoses them again and
keeps them in private staging. Nothing is linked, drafted or published here.
"""

import hashlib
import urllib.error
import urllib.request
from urllib.parse import urlparse

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError

from .crosswalk import (
    STAGE_PERMISSION,
    blocking_reason,
    diagnose_for,
    propose_links,
    stage_snapshot,
)
from .models import SheetSnapshot, SheetSync, Source
from .sheets import load_contract

ALLOWED_HOSTS = ("docs.google.com",)
ALLOWED_HOST_SUFFIXES = (".googleusercontent.com",)
TIMEOUT_SECONDS = 30
REVIEW_SHEETS = ("Data_operations", "Other_data")


class FetchRefused(Exception):
    """The address or the answer is not one this reader accepts."""


def _check_url(url):
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if parsed.scheme != "https" or not (
        host in ALLOWED_HOSTS or host.endswith(ALLOWED_HOST_SUFFIXES)
    ):
        raise FetchRefused("Only https Google Sheets export addresses are read.")


class _CheckedRedirects(urllib.request.HTTPRedirectHandler):
    # Google answers an export with a redirect to a googleusercontent host; nothing else is followed.
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _check_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_csv(url, max_bytes):
    _check_url(url)
    opener = urllib.request.build_opener(_CheckedRedirects)
    request = urllib.request.Request(url, headers={"User-Agent": "mediterranean-rescue-sync"})
    with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
        content = response.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise FetchRefused("The export is larger than the accepted size.")
    return content


def sync_actor(username="sheets-sync"):
    """The account recorded as having saved automatic updates; it cannot sign in."""
    user, created = get_user_model().objects.get_or_create(username=username)
    if created:
        user.set_unusable_password()
        user.save()
    user.user_permissions.add(Permission.objects.get(codename=STAGE_PERMISSION.split(".")[1]))
    return get_user_model().objects.get(pk=user.pk)


def summarize(snapshot):
    """What a new update brings, in counts the team can act on."""
    if snapshot.sheet not in REVIEW_SHEETS:
        return {"rows": snapshot.row_count}
    counts = {"unchanged": 0, "to_look_at": 0, "to_fix": 0, "already_verified": 0}
    for proposal in propose_links(snapshot):
        if proposal.kind == "exact_carry":
            counts["unchanged"] += 1
        elif proposal.kind in ("new", "candidates"):
            counts["to_look_at"] += 1
        elif proposal.kind == "blocked":
            counts["to_fix"] += 1
        else:
            counts["already_verified"] += 1
    return counts


def sync_sheet(*, source, sheet, url, actor, fetch=fetch_csv):
    """Reads one tab once and records what happened. Never raises for an expected failure."""
    max_bytes = load_contract()["input"]["max_bytes"]
    try:
        content = fetch(url, max_bytes)
    except (FetchRefused, urllib.error.URLError, TimeoutError, OSError) as exc:
        message = str(exc) if isinstance(exc, FetchRefused) else "The sheet could not be reached."
        return SheetSync.objects.create(
            source=source, sheet=sheet, status="failed", message=message
        )
    sha = hashlib.sha256(content).hexdigest()
    contract_version = load_contract()["version"]
    known = SheetSnapshot.objects.filter(
        source=source, sheet=sheet, sha256=sha, contract_version=contract_version
    ).first()
    latest = (
        SheetSnapshot.objects.filter(source=source, sheet=sheet).order_by("-created_at").first()
    )
    if known is not None and latest is not None and known.pk == latest.pk:
        return SheetSync.objects.create(
            source=source, sheet=sheet, status="unchanged", snapshot=known, sha256=sha
        )
    try:
        snapshot, _ = stage_snapshot(source=source, sheet=sheet, content=content, actor=actor)
    except ValidationError:
        reason = blocking_reason(diagnose_for(source, sheet, content)) or "invalid"
        return SheetSync.objects.create(
            source=source, sheet=sheet, status="refused", sha256=sha, message=reason
        )
    return SheetSync.objects.create(
        source=source,
        sheet=sheet,
        status="new_data",
        snapshot=snapshot,
        sha256=sha,
        summary=summarize(snapshot),
    )


def sync_all(config, actor=None, fetch=fetch_csv):
    """One pass over every configured tab: {"source": key, "tabs": {sheet: url}}."""
    source = Source.objects.get(key=config["source"])
    actor = actor or sync_actor()
    return [
        sync_sheet(source=source, sheet=sheet, url=url, actor=actor, fetch=fetch)
        for sheet, url in config["tabs"].items()
    ]
