from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from .models import (
    Event,
    Evidence,
    ImportBatch,
    Port,
    PortAlias,
    PublicationAudit,
    RowIdentityLink,
    SheetRow,
    SheetSnapshot,
    Source,
    SourceIdentity,
    StagedRecord,
    Vessel,
    Voyage,
)
from .services import set_publication


def lock_current(model, obj):
    current = model.objects.select_for_update().get(pk=obj.pk)
    if current.updated_at != obj.updated_at:
        raise PermissionDenied(
            "This record changed since the form was opened; reload before saving"
        )
    return current


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "kind", "occurred_on", "status", "source"]
    list_filter = ["status", "kind", "source"]
    search_fields = ["title", "external_id"]
    readonly_fields = ["status", "published_at", "reviewed_by"]
    actions = ["publish_reviewed", "withdraw_reviewed"]

    def has_change_permission(self, request, obj=None):
        return super().has_change_permission(request, obj) and (
            obj is None or obj.status != "published"
        )

    def has_delete_permission(self, request, obj=None):
        return False

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        if change:
            current = lock_current(Event, obj)
            if current.status == "published":
                raise PermissionDenied("Withdraw and review the event before editing")
            obj.status = current.status
            obj.published_at = current.published_at
            obj.reviewed_by_id = current.reviewed_by_id
        super().save_model(request, obj, form, change)

    @admin.action(description="Publier après revue (droits source requis)")
    def publish_reviewed(self, request, queryset):
        for event in queryset:
            try:
                set_publication(
                    event_id=event.pk,
                    actor=request.user,
                    publish=True,
                    reason="Reviewed in Django admin",
                )
            except (PermissionDenied, ValidationError) as exc:
                self.message_user(request, str(exc), level=messages.ERROR)

    @admin.action(description="Retirer de la publication")
    def withdraw_reviewed(self, request, queryset):
        for event in queryset:
            try:
                set_publication(
                    event_id=event.pk,
                    actor=request.user,
                    publish=False,
                    reason="Withdrawn in Django admin",
                )
            except (PermissionDenied, ValidationError) as exc:
                self.message_user(request, str(exc), level=messages.ERROR)


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ["name", "rights_approved", "synthetic"]

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.events.filter(status="published").exists():
            # Rights can be revoked by a source steward; public metadata stays frozen.
            return [
                field.name for field in Source._meta.fields if field.name != "rights_approved"
            ] + ([] if request.user.is_superuser else ["rights_approved"])
        return [] if request.user.is_superuser else ["rights_approved", "license_note", "synthetic"]

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        if change:
            current = lock_current(Source, obj)
            if not request.user.is_superuser:
                obj.rights_approved = current.rights_approved
                obj.license_note = current.license_note
                obj.synthetic = current.synthetic
            if obj.events.filter(status="published").exists() and any(
                name != "rights_approved" for name in form.changed_data
            ):
                raise PermissionDenied("Withdraw published events before changing source metadata")
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return False


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(PublicationAudit, ReadOnlyAdmin)
admin.site.register(ImportBatch, ReadOnlyAdmin)
admin.site.register(StagedRecord, ReadOnlyAdmin)
# Crosswalk records change only through catalog.crosswalk services (reviewed, with a reason).
admin.site.register(SheetSnapshot, ReadOnlyAdmin)
admin.site.register(SheetRow, ReadOnlyAdmin)
admin.site.register(SourceIdentity, ReadOnlyAdmin)
admin.site.register(RowIdentityLink, ReadOnlyAdmin)
admin.site.register(PortAlias, ReadOnlyAdmin)


class FrozenPublishedRelationAdmin(admin.ModelAdmin):
    event_field = ""

    def is_published(self, obj):
        return bool(
            obj and Event.objects.filter(**{self.event_field: obj}, status="published").exists()
        )

    def has_change_permission(self, request, obj=None):
        return super().has_change_permission(request, obj) and not self.is_published(obj)

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        if change:
            lock_current(type(obj), obj)
            linked = Event.objects.select_for_update().filter(**{self.event_field: obj})
            if any(event.status == "published" for event in linked):
                raise PermissionDenied("Withdraw published events before changing related metadata")
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        # Bulk deletion would bypass per-object checks; keep deletion disabled.
        return False


@admin.register(Vessel)
class VesselAdmin(FrozenPublishedRelationAdmin):
    event_field = "vessel"


@admin.register(Voyage)
class VoyageAdmin(FrozenPublishedRelationAdmin):
    event_field = "voyage"


@admin.register(Port)
class PortAdmin(FrozenPublishedRelationAdmin):
    event_field = "port"
    readonly_fields = ["created_from"]


class EvidenceForm(forms.ModelForm):
    class Meta:
        model = Evidence
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        event = cleaned.get("event")
        if event and event.status == "published":
            raise ValidationError("Withdraw and review the event before changing its evidence")
        return cleaned


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    form = EvidenceForm

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        event_ids = {obj.event_id}
        if change:
            current = lock_current(Evidence, obj)
            event_ids.add(current.event_id)
        events = Event.objects.select_for_update().filter(pk__in=event_ids).order_by("pk")
        if any(event.status == "published" for event in events):
            raise PermissionDenied("Withdraw both events before changing evidence")
        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        return super().has_change_permission(request, obj) and not (
            obj and obj.event.status == "published"
        )

    def has_delete_permission(self, request, obj=None):
        return False
