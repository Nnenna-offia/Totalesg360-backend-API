from django.db import migrations


def migrate_framework_indicator_to_requirement_mapping(apps, schema_editor):
    FrameworkIndicator = apps.get_model("indicators", "FrameworkIndicator")
    FrameworkRequirement = apps.get_model("compliance", "FrameworkRequirement")
    IndicatorFrameworkMapping = apps.get_model("compliance", "IndicatorFrameworkMapping")

    for legacy in FrameworkIndicator.objects.all().iterator():
        requirement = (
            FrameworkRequirement.objects.filter(framework_id=legacy.framework_id)
            .order_by("priority", "code")
            .first()
        )

        if requirement is None:
            legacy_code = f"LEGACY_{str(legacy.indicator_id).replace('-', '')[:24]}"
            requirement = FrameworkRequirement.objects.create(
                framework_id=legacy.framework_id,
                code=legacy_code,
                title=f"Legacy mapping for indicator {legacy.indicator_id}",
                description="Auto-created during FrameworkIndicator deprecation migration.",
                pillar=legacy.indicator.pillar,
                is_mandatory=legacy.is_required,
                status="active",
                priority=9999,
            )

        IndicatorFrameworkMapping.objects.get_or_create(
            framework_id=legacy.framework_id,
            requirement_id=requirement.id,
            indicator_id=legacy.indicator_id,
            defaults={
                "mapping_type": "primary",
                "is_primary": True,
                "coverage_percent": 100,
                "is_active": True,
            },
        )


def noop_reverse(apps, schema_editor):
    # FrameworkIndicator is intentionally deprecated and removed.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("compliance", "0002_alter_frameworkrequirement_pillar_and_more"),
        ("indicators", "0005_indicatorvalue"),
    ]

    operations = [
        migrations.RunPython(migrate_framework_indicator_to_requirement_mapping, noop_reverse),
        migrations.DeleteModel(
            name="FrameworkIndicator",
        ),
    ]
