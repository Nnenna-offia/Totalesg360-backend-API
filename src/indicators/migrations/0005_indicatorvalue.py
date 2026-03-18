# Generated migration for creating IndicatorValue model

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('indicators', '0004_indicator_collection_method'),
        ('organizations', '0001_initial'),
        ('submissions', '0002_create_datasubmission'),
    ]

    operations = [
        migrations.CreateModel(
            name='IndicatorValue',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('value', models.FloatField(help_text='Aggregated value from activities')),
                ('metadata', models.JSONField(blank=True, default=dict, help_text='Additional calculation metadata (activity count, last update, etc.)')),
                ('facility', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='indicator_values', to='organizations.facility')),
                ('indicator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='calculated_values', to='indicators.indicator')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='indicator_values', to='organizations.organization')),
                ('reporting_period', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='indicator_values', to='submissions.reportingperiod')),
            ],
            options={
                'verbose_name': 'Indicator Value',
                'verbose_name_plural': 'Indicator Values',
                'db_table': 'indicators_indicatorvalue',
                'unique_together': {('organization', 'indicator', 'reporting_period', 'facility')},
                'indexes': [
                    models.Index(fields=['organization', 'reporting_period'], name='indval__org_period_idx'),
                    models.Index(fields=['indicator'], name='indval__indicator_idx'),
                ],
            },
        ),
    ]
