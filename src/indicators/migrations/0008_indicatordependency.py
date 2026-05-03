from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("indicators", "0007_indicator_calculation_method_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="IndicatorDependency",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "relationship_type",
                    models.CharField(
                        choices=[("aggregation", "Aggregation"), ("conversion", "Conversion")],
                        default="aggregation",
                        max_length=20,
                        db_index=True,
                    ),
                ),
                ("weight", models.FloatField(null=True, blank=True)),
                ("is_active", models.BooleanField(default=True, db_index=True)),
                (
                    "child_indicator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="indicator_dependents",
                        to="indicators.indicator",
                    ),
                ),
                (
                    "parent_indicator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="indicator_dependencies",
                        to="indicators.indicator",
                    ),
                ),
            ],
            options={
                "db_table": "indicators_indicatordependency",
                "verbose_name": "Indicator Dependency",
                "verbose_name_plural": "Indicator Dependencies",
                "unique_together": {("parent_indicator", "child_indicator", "relationship_type")},
            },
        ),
        migrations.AddIndex(
            model_name="indicatordependency",
            index=models.Index(fields=["parent_indicator", "is_active"], name="ind_dep_parent_act_idx"),
        ),
        migrations.AddIndex(
            model_name="indicatordependency",
            index=models.Index(fields=["child_indicator", "is_active"], name="ind_dep_child_act_idx"),
        ),
    ]
