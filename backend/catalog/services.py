from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Event, PublicationAudit


@transaction.atomic
def set_publication(*, event_id, actor, publish: bool, reason: str) -> Event:
    if not actor.is_active or not actor.has_perm("catalog.publish_event"):
        raise PermissionDenied("Publication permission required")
    if not reason.strip():
        raise ValidationError("A review reason is required")
    event = (
        Event.objects.select_for_update(of=("self", "source"))
        .select_related("source", "voyage")
        .get(pk=event_id)
    )
    if publish and (not event.source.rights_approved or not event.source.license_note.strip()):
        raise ValidationError("Source publication rights and license note must be approved")
    event.status = "published" if publish else "withdrawn"
    event.published_at = timezone.now() if publish else event.published_at
    event.reviewed_by = actor
    event.full_clean()
    event.save(update_fields=["status", "published_at", "reviewed_by", "updated_at"])
    PublicationAudit.objects.create(
        event=event,
        actor=actor,
        action=event.status,
        reason=reason,
        snapshot={
            "title": event.title,
            "occurred_on": str(event.occurred_on),
            "people": event.people,
            "source_id": str(event.source_id),
            "source_url": event.source_url,
            "location": event.location.geojson if event.location else None,
            "status": event.status,
        },
    )
    return event
