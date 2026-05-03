from django.db import migrations, models


def migrate_mapping_types(apps, schema_editor):
    Mapping = apps.get_model("compliance", "IndicatorFrameworkMapping")
    Mapping.objects.filter(mapping_type="supporting").update(mapping_type="secondary")
    Mapping.objects.filter(mapping_type="reference").update(mapping_type="derived")


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("compliance", "0002_alter_frameworkrequirement_pillar_and_more"),
    ]

    operations = [
        migrations.RunPython(migrate_mapping_types, noop_reverse),
        migrations.AlterField(
            model_name="indicatorframeworkmapping",
            name="mapping_type",
            field=models.CharField(
                choices=[
                    ("primary", "Primary"),
                    ("secondary", "Secondary"),
                    ("derived", "Derived"),
                ],
                default="primary",
                help_text="Type of mapping (primary/secondary/derived)",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="indicatorframeworkmapping",
            name="coverage_percent",
            field=models.IntegerField(
                default=0,
                help_text="How much of the requirement is covered by this indicator (0-100%)",
            ),
        ),
    ]
