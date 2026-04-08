"""Add quarter field to ReportingPeriod

Generated to match model changes that added an optional `quarter` field.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("submissions", "0007_reportingperiod_year_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="reportingperiod",
            name="quarter",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
