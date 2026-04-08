"""Remove `unit` column from ActivitySubmission.

This migration drops the `unit` column from `submissions_activitysubmission`.
Existing values are not migrated since `ActivityType.unit` is now the source
of truth.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0005_rename_submissions_org_period_type_idx_submissions_organiz_6ac7d3_idx_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='activitysubmission',
            name='unit',
        ),
    ]
