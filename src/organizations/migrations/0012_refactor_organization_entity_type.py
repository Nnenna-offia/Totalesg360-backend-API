from django.db import migrations, models


DEMO_SUBSIDIARY_NAMES = [
    "WACOT Rice",
    "WACOT Limited",
    "Chi Farms",
    "TGI Distri",
    "Fludor Ghana",
    "Titan Trust Bank",
]


def forward(apps, schema_editor):
    Organization = apps.get_model("organizations", "Organization")

    root_qs = Organization.objects.filter(parent__isnull=True).exclude(entity_type="group")
    root_qs.update(entity_type="group")

    child_qs = Organization.objects.filter(parent__isnull=False, entity_type="group")
    child_qs.update(entity_type="subsidiary")

    try:
        group = Organization.objects.get(name="TGI Group")
    except Organization.DoesNotExist:
        return

    if group.entity_type != "group" or group.parent_id is not None:
        group.entity_type = "group"
        group.parent = None
        group.save(update_fields=["entity_type", "parent"])

    Organization.objects.filter(name__in=DEMO_SUBSIDIARY_NAMES).exclude(pk=group.pk).update(
        entity_type="subsidiary",
        parent=group,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0011_rename_organizations_organizatio_type_idx_organizatio_organiz_d4294a_idx_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="organization",
            old_name="organization_type",
            new_name="entity_type",
        ),
        migrations.RemoveIndex(
            model_name="organization",
            name="organizatio_organiz_d4294a_idx",
        ),
        migrations.RemoveIndex(
            model_name="organization",
            name="organizatio_parent__485487_idx",
        ),
        migrations.AlterField(
            model_name="organization",
            name="entity_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("group", "Group"),
                    ("subsidiary", "Subsidiary"),
                    ("facility", "Facility"),
                    ("department", "Department"),
                ],
                db_index=True,
                help_text="Organization type in hierarchy: Group, Subsidiary, Facility, Department",
                max_length=20,
            ),
        ),
        migrations.AddIndex(
            model_name="organization",
            index=models.Index(fields=["entity_type"], name="organizatio_entity__5f19fb_idx"),
        ),
        migrations.AddIndex(
            model_name="organization",
            index=models.Index(fields=["parent", "entity_type"], name="organizatio_parent__cc4134_idx"),
        ),
        migrations.RunPython(forward, migrations.RunPython.noop),
    ]