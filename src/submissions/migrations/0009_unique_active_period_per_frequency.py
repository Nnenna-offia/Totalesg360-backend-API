from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("submissions", "0008_add_quarter_to_reportingperiod"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="reportingperiod",
            constraint=models.UniqueConstraint(
                condition=models.Q(is_active=True),
                fields=("organization", "period_type"),
                name="unique_active_period_per_frequency",
            ),
        ),
    ]