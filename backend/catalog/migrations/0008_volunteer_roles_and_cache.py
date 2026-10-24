"""Volunteer roles as groups, and the shared cache table used by the sign-in limit (ADR 0013).

A coordinator gives a volunteer one or more roles; nobody needs individual permissions. Groups
that already exist keep their members, and their permissions are completed, never removed."""

from django.contrib.auth.management import create_permissions
from django.core.management import call_command
from django.db import migrations

ROLES = {
    "Verify events": [("catalog", "review_identity")],
    "Prepare events": [("catalog", "add_event")],
    "Publish events": [("catalog", "publish_event")],
    "Manual import": [("catalog", "add_sheetsnapshot")],
    "Coordinator": [
        ("auth", "view_user"),
        ("auth", "add_user"),
        ("auth", "change_user"),
        ("auth", "view_group"),
    ],
}


def create_roles(apps, schema_editor):
    # Permissions are normally created after all migrations; make sure they exist first.
    for config in apps.get_app_configs():
        config.models_module = True
        create_permissions(config, verbosity=0, apps=apps)
        config.models_module = None
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    for name, permissions in ROLES.items():
        group, _ = Group.objects.get_or_create(name=name)
        for app_label, codename in permissions:
            group.permissions.add(
                Permission.objects.get(content_type__app_label=app_label, codename=codename)
            )


def create_cache_table(apps, schema_editor):
    call_command("createcachetable", database=schema_editor.connection.alias, verbosity=0)


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("catalog", "0007_plain_labels_and_constraints"),
    ]

    operations = [
        migrations.RunPython(create_roles, migrations.RunPython.noop),
        migrations.RunPython(create_cache_table, migrations.RunPython.noop),
    ]
