# Generated migration for ReportingPeriod refactor to flexible date-based periods
from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone
from datetime import date


def migrate_year_quarter_to_dates(apps, schema_editor):
    """
    Forward migration: Convert existing year/quarter records to date-based records.
    
    Quarter mapping:
    - Q1: Jan 1 - Mar 31
    - Q2: Apr 1 - Jun 30
    - Q3: Jul 1 - Sep 30
    - Q4: Oct 1 - Dec 31
    - Annual (no quarter): Jan 1 - Dec 31
    """
    ReportingPeriod = apps.get_model('submissions', 'ReportingPeriod')
    
    quarter_date_map = {
        1: (1, 1, 3, 31),   # Q1: Jan 1 - Mar 31
        2: (4, 1, 6, 30),   # Q2: Apr 1 - Jun 30
        3: (7, 1, 9, 30),   # Q3: Jul 1 - Sep 30
        4: (10, 1, 12, 31), # Q4: Oct 1 - Dec 31
    }
    
    for period in ReportingPeriod.objects.all():
        year = period.year
        quarter = period.quarter
        
        if quarter and 1 <= quarter <= 4:
            # Quarterly period
            start_month, start_day, end_month, end_day = quarter_date_map[quarter]
            period.name = f"Q{quarter} {year}"
            period.period_type = "QUARTERLY"
            period.start_date = date(year, start_month, start_day)
            period.end_date = date(year, end_month, end_day)
        else:
            # Annual period (no quarter specified)
            period.name = f"{year}"
            period.period_type = "ANNUAL"
            period.start_date = date(year, 1, 1)
            period.end_date = date(year, 12, 31)
        
        period.save(update_fields=['name', 'period_type', 'start_date', 'end_date'])


def reverse_migration_dates_to_year_quarter(apps, schema_editor):
    """
    Reverse migration: Convert date-based records back to year/quarter.
    Only works for quarterly and annual periods.
    """
    ReportingPeriod = apps.get_model('submissions', 'ReportingPeriod')
    
    for period in ReportingPeriod.objects.all():
        # Extract year from start_date
        period.year = period.start_date.year
        
        # Determine quarter from period_type and dates
        if period.period_type == "QUARTERLY":
            if period.start_date.month == 1:
                period.quarter = 1
            elif period.start_date.month == 4:
                period.quarter = 2
            elif period.start_date.month == 7:
                period.quarter = 3
            elif period.start_date.month == 10:
                period.quarter = 4
            else:
                period.quarter = None  # Unknown quarter
        else:
            # Annual or other types: no quarter
            period.quarter = None
        
        period.save(update_fields=['year', 'quarter'])


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0003_activitysubmission_and_more'),
    ]

    operations = [
        # Step 1: Add new fields (nullable initially)
        migrations.AddField(
            model_name='reportingperiod',
            name='name',
            field=models.CharField(
                max_length=120,
                help_text="Human readable label e.g. Week 1 2025, Jan 2025, Q1 2025",
                null=True,
                blank=True
            ),
        ),
        migrations.AddField(
            model_name='reportingperiod',
            name='period_type',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('DAILY', 'Daily'),
                    ('WEEKLY', 'Weekly'),
                    ('BI_WEEKLY', 'Bi-Weekly'),
                    ('MONTHLY', 'Monthly'),
                    ('QUARTERLY', 'Quarterly'),
                    ('SEMI_ANNUAL', 'Semi-Annual'),
                    ('ANNUAL', 'Annual'),
                    ('CUSTOM', 'Custom'),
                ],
                db_index=True,
                null=True,
                blank=True
            ),
        ),
        migrations.AddField(
            model_name='reportingperiod',
            name='start_date',
            field=models.DateField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='reportingperiod',
            name='end_date',
            field=models.DateField(null=True, blank=True),
        ),
        
        # Step 2: Migrate existing data from year/quarter to new fields
        migrations.RunPython(
            migrate_year_quarter_to_dates,
            reverse_code=reverse_migration_dates_to_year_quarter,
        ),
        
        # Step 3: Make new fields non-nullable
        migrations.AlterField(
            model_name='reportingperiod',
            name='name',
            field=models.CharField(
                max_length=120,
                help_text="Human readable label e.g. Week 1 2025, Jan 2025, Q1 2025"
            ),
        ),
        migrations.AlterField(
            model_name='reportingperiod',
            name='period_type',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('DAILY', 'Daily'),
                    ('WEEKLY', 'Weekly'),
                    ('BI_WEEKLY', 'Bi-Weekly'),
                    ('MONTHLY', 'Monthly'),
                    ('QUARTERLY', 'Quarterly'),
                    ('SEMI_ANNUAL', 'Semi-Annual'),
                    ('ANNUAL', 'Annual'),
                    ('CUSTOM', 'Custom'),
                ],
                db_index=True
            ),
        ),
        migrations.AlterField(
            model_name='reportingperiod',
            name='start_date',
            field=models.DateField(),
        ),
        migrations.AlterField(
            model_name='reportingperiod',
            name='end_date',
            field=models.DateField(),
        ),
        
        # Step 4: Remove old unique_together constraint
        migrations.AlterUniqueTogether(
            name='reportingperiod',
            unique_together=set(),
        ),
        
        # Step 5: Remove old fields
        migrations.RemoveField(
            model_name='reportingperiod',
            name='year',
        ),
        migrations.RemoveField(
            model_name='reportingperiod',
            name='quarter',
        ),
        
        # Step 6: Add new unique constraint and indexes
        migrations.AlterUniqueTogether(
            name='reportingperiod',
            unique_together={('organization', 'name')},
        ),
        migrations.AddIndex(
            model_name='reportingperiod',
            index=models.Index(fields=['organization', 'period_type'], name='submissions_org_period_type_idx'),
        ),
        migrations.AddIndex(
            model_name='reportingperiod',
            index=models.Index(fields=['start_date', 'end_date'], name='submissions_start_end_date_idx'),
        ),
    ]
