from django.db import migrations, models


def ensure_no_null_indicators(apps, schema_editor):
    ActivityType = apps.get_model("activities", "ActivityType")
    Indicator = apps.get_model("indicators", "Indicator")

    # Create a placeholder indicator to assign to legacy ActivityType rows
    # Use literal values for choice fields because historical models
    # in migrations don't expose the enum attributes.
    placeholder, created = Indicator.objects.get_or_create(
        code="ACTIVITY_PLACEHOLDER",
        defaults={
            "name": "Placeholder Indicator for legacy ActivityType",
            "pillar": "ENV",
            "data_type": "number",
            "unit": None,
        },
    )

    # Backfill any ActivityType rows missing an indicator to point to the placeholder.
    ActivityType.objects.filter(indicator__isnull=True).update(indicator_id=placeholder.id)


class Migration(migrations.Migration):

    dependencies = [
        ("activities", "0002_activitytype_indicator"),
    ]

    operations = [
        migrations.RunPython(ensure_no_null_indicators, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name="activitytype",
            name="indicator",
            field=models.ForeignKey(
                on_delete=models.PROTECT,
                related_name="activity_types",
                to="indicators.indicator",
            ),
        ),
    ]
