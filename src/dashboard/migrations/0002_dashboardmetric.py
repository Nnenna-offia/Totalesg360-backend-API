from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0001_initial'),
        ('organizations', '0003_rename_regulatory_coverage_to_primary_reporting_focus'),
        ('submissions', '0003_activitysubmission_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='DashboardMetric',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pillar', models.CharField(blank=True, max_length=8, null=True)),
                ('environmental_score', models.FloatField(blank=True, null=True)),
                ('social_score', models.FloatField(blank=True, null=True)),
                ('governance_score', models.FloatField(blank=True, null=True)),
                ('overall_esg_score', models.FloatField(blank=True, null=True)),
                ('calculated_at', models.DateTimeField(db_index=True, auto_now_add=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='organizations.organization')),
                ('reporting_period', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='submissions.reportingperiod')),
            ],
            options={
                'db_table': 'dashboard_dashboardmetric',
            },
        ),
        migrations.AddIndex(
            model_name='dashboardmetric',
            index=models.Index(fields=['organization', 'reporting_period'], name='dashboard_organiz_8e1b2_idx'),
        ),
        migrations.AddIndex(
            model_name='dashboardmetric',
            index=models.Index(fields=['calculated_at'], name='dashboard_calculated_at_idx'),
        ),
    ]
