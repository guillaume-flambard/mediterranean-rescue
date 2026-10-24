import uuid

from django.conf import settings
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, URLValidator
from django.db.models import Q
from django.utils.translation import gettext_lazy as _


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Source(UUIDModel):
    key = models.SlugField(_("short key"), unique=True)
    name = models.CharField(_("name"), max_length=200, help_text=_("As shown to the public."))
    url = models.URLField(_("address"), max_length=1000)
    license_note = models.TextField(
        _("licence and agreement"),
        blank=True,
        help_text=_("Who agreed to the publication, when, and under which terms."),
    )
    rights_approved = models.BooleanField(
        _("publication agreed"),
        default=False,
        help_text=_(
            "Tick only once the data owner has agreed in writing. Until then nothing from this "
            "source can be published."
        ),
    )
    synthetic = models.BooleanField(
        _("fictitious data"),
        default=False,
        help_text=_("Training data: shown publicly only in training mode."),
    )

    class Meta:
        verbose_name = _("source")
        verbose_name_plural = _("sources")
        constraints = [
            models.CheckConstraint(
                condition=Q(rights_approved=False) | ~Q(license_note__regex=r"^\s*$"),
                name="approved_source_has_licence_note",
            )
        ]

    def clean(self):
        if self.rights_approved and not self.license_note.strip():
            raise ValidationError("Approved publication rights need an explicit license note")

    def __str__(self):
        return self.name


class Vessel(UUIDModel):
    name = models.CharField(_("name"), max_length=200)
    imo = models.CharField(_("IMO number"), max_length=7, blank=True)

    class Meta:
        verbose_name = _("ship")
        verbose_name_plural = _("ships")

    def __str__(self):
        return self.name


class Port(UUIDModel):
    name = models.CharField(_("name"), max_length=200)
    country_code = models.CharField(_("country code"), max_length=2, blank=True)
    location = models.PointField(_("position"), srid=4326, null=True, blank=True)
    # Whether the location was taken from the source row (format kept on that row) or typed
    # by the reviewer; empty for ports created before the crosswalk.
    location_source = models.CharField(
        max_length=16,
        blank=True,
        choices=[("sheet_row", "Source row"), ("reviewer", "Reviewer")],
    )
    # Data_ports row the port was approved from, when it came from a Sheets snapshot.
    created_from = models.ForeignKey(
        "SheetRow", null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )

    class Meta:
        verbose_name = _("port")
        verbose_name_plural = _("ports")

    def __str__(self):
        return self.name


class Voyage(UUIDModel):
    vessel = models.ForeignKey(Vessel, on_delete=models.PROTECT, related_name="voyages")
    title = models.CharField(max_length=200)
    started_on = models.DateField()
    ended_on = models.DateField(null=True, blank=True)
    logbook_url = models.URLField(max_length=1000, blank=True)

    class Meta:
        verbose_name = _("voyage")
        verbose_name_plural = _("voyages")
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
    kind = models.CharField(_("kind"), max_length=20, choices=EventKind.choices)
    occurred_on = models.DateField(_("date"), db_index=True)
    title = models.CharField(_("title"), max_length=240)
    summary = models.TextField(_("summary"), blank=True)
    source_url = models.URLField(_("source address"), max_length=1000)
    location = models.PointField(_("position"), srid=4326, null=True, blank=True)
    location_precision = models.CharField(
        max_length=16,
        choices=[
            ("unknown", "Inconnue"),
            ("approximate", "Approximative"),
            ("reported", "Rapportée"),
        ],
        default="unknown",
    )
    people = models.PositiveIntegerField(
        _("people"), null=True, blank=True, help_text=_("Leave empty when not known; never 0.")
    )
    women = models.PositiveIntegerField(_("women"), null=True, blank=True)
    minors = models.PositiveIntegerField(_("minors"), null=True, blank=True)
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
        verbose_name = _("event")
        verbose_name_plural = _("events")
        ordering = ["-occurred_on", "id"]
        permissions = [("publish_event", "Can publish or withdraw reviewed events")]
        constraints = [
            models.CheckConstraint(condition=Q(kind__in=EventKind.values), name="event_kind_known"),
            models.CheckConstraint(
                condition=Q(status__in=["draft", "published", "withdrawn"]),
                name="event_status_known",
            ),
            # A position always says how precise it is; no position, no precision.
            models.CheckConstraint(
                condition=(Q(location__isnull=True) & Q(location_precision="unknown"))
                | (Q(location__isnull=False) & ~Q(location_precision="unknown")),
                name="event_position_has_precision",
            ),
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
    label = models.CharField(_("label"), max_length=200)
    url = models.URLField(_("address"), max_length=1000)

    class Meta:
        verbose_name = _("source document")
        verbose_name_plural = _("source documents")

    def __str__(self):
        return self.label


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
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name=_("decided by")
    )
    action = models.CharField(_("decision"), max_length=20)
    reason = models.TextField(_("reason"))
    snapshot = models.JSONField(_("event as decided"))
    created_at = models.DateTimeField(_("decided at"), auto_now_add=True)

    class Meta:
        verbose_name = _("publication decision")
        verbose_name_plural = _("publication decisions")

    def __str__(self):
        return f"{self.action} · {self.event} · {self.created_at:%Y-%m-%d}"


SHEETS = [
    ("Data_operations", "Data_operations"),
    ("Other_data", "Other_data"),
    ("Data_ports", "Data_ports"),
]


class SheetSnapshot(UUIDModel):
    """One diagnosed Sheets export in private staging; raw cells never leave it."""

    source = models.ForeignKey(Source, on_delete=models.PROTECT, related_name="sheet_snapshots")
    sheet = models.CharField(max_length=32, choices=SHEETS)
    sha256 = models.CharField(max_length=64)
    contract_version = models.CharField(max_length=40)
    source_read = models.CharField(max_length=16)
    byte_count = models.PositiveIntegerField()
    row_count = models.PositiveIntegerField()
    # Header row as received, so a row can be shown with its exact column names.
    header_cells = models.JSONField(default=list, blank=True)
    staged_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source", "sheet", "sha256", "contract_version"],
                name="sheet_snapshot_idempotent",
            )
        ]

    def __str__(self):
        return f"{self.sheet}@{self.sha256[:12]}"


class SheetSync(UUIDModel):
    """One scheduled reading of a Google Sheets tab and what it found (ADR 0012)."""

    source = models.ForeignKey(Source, on_delete=models.PROTECT, related_name="sheet_syncs")
    sheet = models.CharField(max_length=32, choices=SHEETS)
    status = models.CharField(
        max_length=16,
        choices=[
            ("new_data", "New data saved"),
            ("unchanged", "Unchanged"),
            ("refused", "Refused by the checks"),
            ("failed", "Could not read"),
        ],
    )
    snapshot = models.ForeignKey(
        SheetSnapshot, on_delete=models.PROTECT, null=True, blank=True, related_name="syncs"
    )
    sha256 = models.CharField(max_length=64, blank=True)
    # Counts only (to look at, unchanged, to fix); never source values.
    summary = models.JSONField(default=dict, blank=True)
    message = models.CharField(max_length=300, blank=True)

    class Meta:
        indexes = [models.Index(fields=["source", "sheet", "-created_at"])]

    def __str__(self):
        return f"{self.sheet} {self.status} {self.created_at:%Y-%m-%d %H:%M}"


class SheetRow(UUIDModel):
    snapshot = models.ForeignKey(SheetSnapshot, on_delete=models.PROTECT, related_name="rows")
    line = models.PositiveIntegerField(validators=[MinValueValidator(2)])
    raw_cells = models.JSONField()
    candidate = models.JSONField(null=True, blank=True)
    # SHA-256 of the canonical candidate JSON; empty when the row could not be normalized.
    fingerprint = models.CharField(max_length=64, blank=True, db_index=True)
    error_codes = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["snapshot", "line"]
        constraints = [
            models.UniqueConstraint(fields=["snapshot", "line"], name="sheet_row_location")
        ]

    @property
    def row_ref(self):
        return f"{self.snapshot.sheet}@sha256:{self.snapshot.sha256}#L{self.line}"

    def __str__(self):
        return self.row_ref


class LogbookEvidence(UUIDModel):
    """Where a row rebuilt from the public logbook comes from (ADR 0014): the page, the entry and
    a short quote, shown next to the row so a volunteer can check it against the source."""

    row = models.OneToOneField(SheetRow, on_delete=models.CASCADE, related_name="logbook")
    source_url = models.URLField(max_length=1000)
    rotation = models.CharField(max_length=200)
    logged_at = models.CharField(max_length=40, help_text="Day and time of the logbook entry.")
    quote = models.TextField(max_length=500)
    to_check = models.TextField(blank=True)

    def __str__(self):
        return f"{self.rotation} {self.logged_at}"


class SourceIdentity(UUIDModel):
    """Durable identity we assign to a source record; created only by human approval."""

    source = models.ForeignKey(Source, on_delete=models.PROTECT, related_name="identities")
    sheet = models.CharField(max_length=32, choices=SHEETS)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    reason = models.TextField()
    # Draft event created from this identity (ADR 0006); never overwritten once set.
    event = models.OneToOneField(
        Event, null=True, blank=True, on_delete=models.PROTECT, related_name="source_identity"
    )
    drafted_from = models.ForeignKey(
        "SheetRow", null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    drafted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    drafted_at = models.DateTimeField(null=True, blank=True)
    draft_reason = models.TextField(blank=True)
    # Translated field values the draft holds from its source row (after the last applied
    # revision); a later difference on the event means a hand edit.
    drafted_values = models.JSONField(default=dict, blank=True)

    class Meta:
        permissions = [
            ("review_identity", "Can approve source identities, row links and port aliases")
        ]
        constraints = [
            models.CheckConstraint(
                condition=~Q(reason__regex=r"^\s*$"), name="source_identity_has_reason"
            ),
            models.CheckConstraint(
                condition=(
                    Q(event__isnull=True)
                    & Q(drafted_from__isnull=True)
                    & Q(drafted_by__isnull=True)
                    & Q(drafted_at__isnull=True)
                    & Q(draft_reason="")
                )
                | (
                    Q(event__isnull=False)
                    & Q(drafted_from__isnull=False)
                    & Q(drafted_by__isnull=False)
                    & Q(drafted_at__isnull=False)
                    & ~Q(draft_reason__regex=r"^\s*$")
                ),
                name="source_identity_draft_traced",
            ),
        ]

    @property
    def external_id(self):
        return f"{self.sheet}:{self.pk}"

    def __str__(self):
        return self.external_id


class RowIdentityLink(UUIDModel):
    """Approved decision that a snapshot row describes a source identity."""

    row = models.OneToOneField(SheetRow, on_delete=models.PROTECT, related_name="identity_link")
    # Copy of row.snapshot so the database can refuse one identity twice in a snapshot.
    snapshot = models.ForeignKey(SheetSnapshot, on_delete=models.PROTECT, related_name="+")
    identity = models.ForeignKey(SourceIdentity, on_delete=models.PROTECT, related_name="links")
    match = models.CharField(
        max_length=16,
        choices=[
            ("new", "New identity"),
            ("exact_carry", "Unchanged content carried over"),
            ("reviewed_match", "Reviewed match"),
        ],
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    reason = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["identity", "snapshot"], name="identity_once_per_snapshot"
            ),
            models.CheckConstraint(
                condition=~Q(reason__regex=r"^\s*$"), name="row_link_has_reason"
            ),
        ]

    def save(self, *args, **kwargs):
        # Guard writes that bypass catalog.crosswalk (shell, scripts).
        row = SheetRow.objects.select_related("snapshot").get(pk=self.row_id)
        identity = SourceIdentity.objects.get(pk=self.identity_id)
        if self.snapshot_id != row.snapshot_id:
            raise ValidationError("Link snapshot must be the row snapshot")
        if (identity.source_id, identity.sheet) != (row.snapshot.source_id, row.snapshot.sheet):
            raise ValidationError("Identity belongs to another source or sheet")
        super().save(*args, **kwargs)


class PortAlias(UUIDModel):
    """Approved reading of an exact source port label.

    Port_disembarkation holds ports, but also several ports at once, transfer vessels and
    regions: a label maps to one or more ports, to a vessel, or is classified as not a port.
    """

    source = models.ForeignKey(Source, on_delete=models.PROTECT, related_name="port_aliases")
    label = models.CharField(max_length=200)
    target = models.CharField(
        max_length=16,
        choices=[
            ("ports", "One or more ports"),
            ("vessel", "A vessel (transfer)"),
            ("not_a_port", "Not a port (region or unknown)"),
        ],
    )
    ports = models.ManyToManyField(
        Port, blank=True, related_name="aliases", through="PortAliasPort"
    )
    vessel = models.ForeignKey(
        Vessel, null=True, blank=True, on_delete=models.PROTECT, related_name="port_aliases"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    reason = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["source", "label"], name="port_alias_per_source"),
            models.CheckConstraint(
                condition=~Q(reason__regex=r"^\s*$"), name="port_alias_has_reason"
            ),
            models.CheckConstraint(
                condition=(Q(target="vessel") & Q(vessel__isnull=False))
                | (~Q(target="vessel") & Q(vessel__isnull=True)),
                name="port_alias_vessel_target",
            ),
        ]

    def __str__(self):
        return f"{self.label} ({self.target})"


class PortAliasPort(models.Model):
    # Explicit through table: deleting a port never silently empties an approved reading.
    alias = models.ForeignKey(PortAlias, on_delete=models.CASCADE)
    port = models.ForeignKey(Port, on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["alias", "port"], name="port_alias_port_once")
        ]


class EventRevision(UUIDModel):
    """Reviewed decision on a corrected source row for an existing draft (ADR 0007)."""

    event = models.ForeignKey(Event, on_delete=models.PROTECT, related_name="revisions")
    identity = models.ForeignKey(SourceIdentity, on_delete=models.PROTECT, related_name="revisions")
    from_row = models.ForeignKey(SheetRow, on_delete=models.PROTECT, related_name="+")
    to_row = models.ForeignKey(SheetRow, on_delete=models.PROTECT, related_name="+")
    # {field: [value before, value after]} for the translated fields that differ.
    changes = models.JSONField(default=dict, blank=True)
    decision = models.CharField(
        max_length=16, choices=[("applied", "Applied"), ("rejected", "Rejected")]
    )
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    reason = models.TextField()

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.CheckConstraint(
                condition=~Q(reason__regex=r"^\s*$"), name="event_revision_has_reason"
            ),
            models.CheckConstraint(
                condition=Q(decision__in=["applied", "rejected"]), name="event_revision_decision"
            ),
        ]
