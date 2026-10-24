from django import forms
from django.contrib import admin, messages
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from .models import (
    Event,
    EventRevision,
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

# The administration is for the coordinator and the technical lead; volunteers work in the team
# space. Its titles say so in plain words.
admin.site.site_header = _("Mediterranean Rescue administration")
admin.site.site_title = _("Mediterranean Rescue administration")
admin.site.index_title = _("Accounts, roles and source agreements")


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
    date_hierarchy = "occurred_on"
    readonly_fields = ["status", "published_at", "reviewed_by"]
    actions = ["publish_reviewed", "withdraw_reviewed"]

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        if obj is not None and hasattr(obj, "source_identity"):
            # A draft from a source identity keeps the identity's source and external id.
            fields += ["source", "external_id"]
        return fields

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

    def decide(self, request, queryset, publish):
        """Ask for a reason on an intermediate page, then record one decision per event."""
        reason = request.POST.get("reason", "").strip() if "apply" in request.POST else ""
        if not reason:
            return TemplateResponse(
                request,
                "admin/catalog/event/publication_reason.html",
                {
                    **self.admin_site.each_context(request),
                    "title": _("Publish events") if publish else _("Withdraw events"),
                    "events": queryset,
                    "action": request.POST.get("action"),
                    "publish": publish,
                    "missing": "apply" in request.POST,
                    "checkbox_name": ACTION_CHECKBOX_NAME,
                    "opts": self.model._meta,
                },
            )
        done = 0
        for event in queryset:
            try:
                set_publication(
                    event_id=event.pk, actor=request.user, publish=publish, reason=reason
                )
                done += 1
            except (PermissionDenied, ValidationError) as exc:
                self.message_user(request, f"{event}: {exc}", level=messages.ERROR)
        if done:
            self.message_user(
                request,
                ngettext("%(count)d event updated.", "%(count)d events updated.", done)
                % {"count": done},
                level=messages.SUCCESS,
            )
        return None

    @admin.action(description=_("Publish, with a reason (source agreement required)"))
    def publish_reviewed(self, request, queryset):
        return self.decide(request, queryset, publish=True)

    @admin.action(description=_("Withdraw from the public site, with a reason"))
    def withdraw_reviewed(self, request, queryset):
        return self.decide(request, queryset, publish=False)


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ["name", "rights_approved", "synthetic"]
    search_fields = ["name", "key"]

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


@admin.register(PublicationAudit)
class PublicationAuditAdmin(ReadOnlyAdmin):
    list_display = ["created_at", "action", "event", "actor", "reason"]
    list_filter = ["action"]
    search_fields = ["reason", "event__title", "actor__username"]
    date_hierarchy = "created_at"


admin.site.register(ImportBatch, ReadOnlyAdmin)
admin.site.register(StagedRecord, ReadOnlyAdmin)
# Crosswalk records change only through catalog.crosswalk services (reviewed, with a reason).
admin.site.register(SheetSnapshot, ReadOnlyAdmin)
admin.site.register(SheetRow, ReadOnlyAdmin)
admin.site.register(SourceIdentity, ReadOnlyAdmin)
admin.site.register(RowIdentityLink, ReadOnlyAdmin)
admin.site.register(PortAlias, ReadOnlyAdmin)
admin.site.register(EventRevision, ReadOnlyAdmin)


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
    list_display = ["name", "imo"]
    search_fields = ["name", "imo"]


@admin.register(Voyage)
class VoyageAdmin(FrozenPublishedRelationAdmin):
    event_field = "voyage"
    list_display = ["title", "vessel", "started_on", "ended_on"]
    search_fields = ["title", "vessel__name"]
    autocomplete_fields = ["vessel"]


@admin.register(Port)
class PortAdmin(FrozenPublishedRelationAdmin):
    event_field = "port"
    readonly_fields = ["created_from"]
    list_display = ["name", "country_code"]
    search_fields = ["name"]


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


# Volunteer accounts. A coordinator (a staff member in the "Coordinator" group) creates accounts,
# activates or deactivates them and gives volunteer roles; only a superuser can make staff,
# superusers, coordinators or individual permissions. Django warns that editing users is close to
# superuser power, so everything else is out of the coordinator's reach.
COORDINATOR_ROLE = "Coordinator"
# Roles only a superuser may give or take: otherwise a coordinator could create an account with a
# password they know, make it a publisher and publish under another name.
RESTRICTED_ROLES = (COORDINATOR_ROLE, "Publish events")
User = get_user_model()
admin.site.unregister(User)


@admin.register(User)
class VolunteerUserAdmin(UserAdmin):
    list_display = ["username", "first_name", "last_name", "is_active", "roles"]
    list_filter = ["is_active", "groups"]

    @admin.display(description=_("roles"))
    def roles(self, obj):
        return ", ".join(group.name for group in obj.groups.all())

    def get_queryset(self, request):
        queryset = super().get_queryset(request).prefetch_related("groups")
        if request.user.is_superuser:
            return queryset
        return queryset.filter(is_staff=False, is_superuser=False)

    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser or obj is None:
            return super().get_fieldsets(request, obj)
        return [
            (None, {"fields": ["username", "password"]}),
            (_("Person"), {"fields": ["first_name", "last_name", "email"]}),
            (
                _("Access"),
                {
                    "fields": ["is_active", "groups"],
                    "description": _(
                        "Roles you can give: Verify events, Prepare events, Manual import. "
                        "Publish events is given by a superuser. Untick Active to close an "
                        "account without deleting its history."
                    ),
                },
            ),
        ]

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "groups" and not request.user.is_superuser:
            kwargs["queryset"] = Group.objects.exclude(name__in=RESTRICTED_ROLES)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def has_change_permission(self, request, obj=None):
        if obj is not None and not request.user.is_superuser and (obj.is_staff or obj.is_superuser):
            return False
        return super().has_change_permission(request, obj)

    def user_change_password(self, request, id, form_url=""):
        # A publisher's password is set by a superuser only, so nobody can act in their name.
        user = self.get_object(request, id)
        if (
            user is not None
            and not request.user.is_superuser
            and user.groups.filter(name__in=RESTRICTED_ROLES).exists()
        ):
            raise PermissionDenied(_("Only a superuser can change this person's password."))
        return super().user_change_password(request, id, form_url)

    def save_related(self, request, form, formsets, change):
        # The coordinator's form does not offer the restricted roles: keep the ones already held.
        kept = []
        if change and not request.user.is_superuser:
            kept = list(form.instance.groups.filter(name__in=RESTRICTED_ROLES))
        super().save_related(request, form, formsets, change)
        if kept:
            form.instance.groups.add(*kept)

    def has_delete_permission(self, request, obj=None):
        # Accounts are deactivated, never deleted: their decisions stay attributed.
        return False

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.is_staff = False
            obj.is_superuser = False
        super().save_model(request, obj, form, change)
