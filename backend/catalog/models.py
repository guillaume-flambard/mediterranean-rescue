import uuid

from django.conf import settings
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, URLValidator
from django.db.models import Q


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Source(UUIDModel):
    key = models.SlugField(unique=True)
    name = models.CharField(max_length=200)
    url = models.URLField(max_length=1000)
    license_note = models.TextField(blank=True)
    rights_approved = models.BooleanField(default=False)
    synthetic = models.BooleanField(default=False)

    def clean(self):
        if self.rights_approved and not self.license_note.strip():
            raise ValidationError("Approved publication rights need an explicit license note")

    def __str__(self):
        return self.name


class Vessel(UUIDModel):
    name = models.CharField(max_length=200)
    imo = models.CharField(max_length=7, blank=True)

    def __str__(self):
        return self.name


class Port(UUIDModel):
    name = models.CharField(max_length=200)
    country_code = models.CharField(max_length=2, blank=True)
    location = models.PointField(srid=4326, null=True, blank=True)

    def __str__(self):
        return self.name


class Voyage(UUIDModel):
    vessel = models.ForeignKey(Vessel, on_delete=models.PROTECT, related_name="voyages")
    title = models.CharField(max_length=200)
    started_on = models.DateField()
    ended_on = models.DateField(null=True, blank=True)
    logbook_url = models.URLField(max_length=1000, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(ended_on__isnull=True) | Q(ended_on__gte=models.F("started_on")),
                name="voyage_dates_ordered",
            )
        ]

    def __str__(self):
        return self.title


class EventKind(models.TextChoices):
    RESCUE = "rescue", "Sauvetage"
    TRANSFER = "transfer", "Transfert"
    MEDEVAC = "medevac", "Évacuation médicale"
    INCIDENT = "incident", "Incident"
    SHIPWRECK = "shipwreck", "Naufrage"
    DEAD_MISSING = "dead_missing", "Décès / disparitions"


class EventQuerySet(models.QuerySet):
    def public(self):
        return self.filter(
            status="published",
            source__rights_approved=True,
            source__synthetic=settings.DATA_MODE == "training",
        ).exclude(source__license_note__regex=r"^\s*$")


class Event(UUIDModel):
    source = models.ForeignKey(Source, on_delete=models.PROTECT, related_name="events")
    external_id = models.CharField(max_length=200)
    kind = models.CharField(max_length=20, choices=EventKind.choices)
    occurred_on = models.DateField(db_index=True)
    title = models.CharField(max_length=240)
    summary = models.TextField(blank=True)
    source_url = models.URLField(max_length=1000)
    location = models.PointField(srid=4326, null=True, blank=True)
    location_precision = models.CharField(
        max_length=16,
        choices=[
            ("unknown", "Inconnue"),
            ("approximate", "Approximative"),
            ("reported", "Rapportée"),
        ],
        default="unknown",
    )
    people = models.PositiveIntegerField(null=True, blank=True)
    women = models.PositiveIntegerField(null=True, blank=True)
    minors = models.PositiveIntegerField(null=True, blank=True)
    vessel = models.ForeignKey(Vessel, null=True, blank=True, on_delete=models.PROTECT)
    voyage = models.ForeignKey(Voyage, null=True, blank=True, on_delete=models.PROTECT)
    port = models.ForeignKey(Port, null=True, blank=True, on_delete=models.PROTECT)
    status = models.CharField(
        max_length=12,
        choices=[("draft", "Brouillon"), ("published", "Publié"), ("withdrawn", "Retiré")],
        default="draft",
        db_index=True,
    )
    published_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT
    )
    objects = EventQuerySet.as_manager()

    class Meta:
        ordering = ["-occurred_on", "id"]
        permissions = [("publish_event", "Can publish or withdraw reviewed events")]
        constraints = [
            models.UniqueConstraint(fields=["source", "external_id"], name="event_source_identity"),
            models.CheckConstraint(
                condition=~Q(status="published")
                | (Q(published_at__isnull=False) & Q(reviewed_by__isnull=False)),
                name="published_event_has_review",
            ),
            models.CheckConstraint(
                condition=Q(people__isnull=True)
                | Q(women__isnull=True)
                | Q(women__lte=models.F("people")),
                name="women_within_total",
            ),
            models.CheckConstraint(
                condition=Q(people__isnull=True)
                | Q(minors__isnull=True)
                | Q(minors__lte=models.F("people")),
                name="minors_within_total",
            ),
        ]
        indexes = [models.Index(fields=["status", "occurred_on"], name="event_public_date")]

    def clean(self):
        URLValidator(schemes=["https", "http"])(self.source_url)
        if self.location:
            if not (-180 <= self.location.x <= 180 and -90 <= self.location.y <= 90):
                raise ValidationError("Invalid WGS84 coordinates")
            if self.location_precision == "unknown":
                raise ValidationError("A position needs an explicit precision")
        elif self.location_precision != "unknown":
            raise ValidationError("Position precision must be unknown without a position")
        if self.voyage_id and self.vessel_id and self.voyage.vessel_id != self.vessel_id:
            raise ValidationError("Voyage and event vessels differ")

    def __str__(self):
        return self.title


class Evidence(UUIDModel):
    event = models.ForeignKey(Event, related_name="evidence", on_delete=models.CASCADE)
    label = models.CharField(max_length=200)
    url = models.URLField(max_length=1000)


class ImportBatch(UUIDModel):
    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    checksum = models.CharField(max_length=64)
    contract_version = models.CharField(max_length=16, default="1")
    status = models.CharField(
        max_length=16, default="staged", choices=[("staged", "En attente"), ("applied", "Appliqué")]
    )
    row_count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["source", "checksum"], name="import_content_idempotent")
        ]


class StagedRecord(UUIDModel):
    batch = models.ForeignKey(ImportBatch, related_name="records", on_delete=models.CASCADE)
    ordinal = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    payload = models.JSONField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["batch", "ordinal"], name="import_row_identity")
        ]


class PublicationAudit(models.Model):
    event = models.ForeignKey(Event, on_delete=models.PROTECT, related_name="audit")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=20)
    reason = models.TextField()
    snapshot = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
