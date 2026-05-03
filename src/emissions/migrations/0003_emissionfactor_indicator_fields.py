from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("emissions", "0002_initial"),
        ("indicators", "0007_indicator_calculation_method_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="emissionfactor",
            name="activity_type",
            field=models.ForeignKey(
                to="activities.activitytype",
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="emission_factors",
            ),
        ),
        migrations.AddField(
            model_name="emissionfactor",
            name="factor_value",
            field=models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True),
        ),
        migrations.AddField(
            model_name="emissionfactor",
            name="indicator",
            field=models.ForeignKey(
                to="indicators.indicator",
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="emission_factors",
            ),
        ),
        migrations.AddField(
            model_name="emissionfactor",
            name="unit_input",
            field=models.CharField(max_length=50, blank=True, default=""),
        ),
        migrations.AddField(
            model_name="emissionfactor",
            name="unit_output",
            field=models.CharField(max_length=50, blank=True, default=""),
        ),
    ]
