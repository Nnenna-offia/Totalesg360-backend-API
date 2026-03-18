from django.db import migrations, models
import uuid
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('organizations', '0001_initial'),
        ('submissions', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DashboardSnapshot',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('snapshot_date', models.DateTimeField(db_index=True)),
                ('data', models.JSONField(default=dict, blank=True)),
                ('source', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('facility', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='organizations.facility')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='organizations.organization')),
                ('reporting_period', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='submissions.reportingperiod')),
            ],
            options={'db_table': 'dashboard_dashboardsnapshot'},
        ),
        migrations.CreateModel(
            name='TargetSnapshot',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('snapshot_date', models.DateTimeField(db_index=True)),
                ('data', models.JSONField(default=dict, blank=True)),
                ('source', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('facility', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='organizations.facility')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='organizations.organization')),
                ('reporting_period', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='submissions.reportingperiod')),
            ],
            options={'db_table': 'dashboard_targetsnapshot'},
        ),
        migrations.CreateModel(
            name='EmissionSnapshot',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('snapshot_date', models.DateTimeField(db_index=True)),
                ('data', models.JSONField(default=dict, blank=True)),
                ('source', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('facility', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='organizations.facility')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='organizations.organization')),
                ('reporting_period', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='submissions.reportingperiod')),
            ],
            options={'db_table': 'dashboard_emissionsnapshot'},
        ),
        migrations.CreateModel(
            name='IndicatorSnapshot',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('snapshot_date', models.DateTimeField(db_index=True)),
                ('data', models.JSONField(default=dict, blank=True)),
                ('source', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('facility', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='organizations.facility')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='organizations.organization')),
                ('reporting_period', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='submissions.reportingperiod')),
            ],
            options={'db_table': 'dashboard_indicatorsnapshot'},
        ),
        migrations.CreateModel(
            name='ComplianceSnapshot',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('snapshot_date', models.DateTimeField(db_index=True)),
                ('data', models.JSONField(default=dict, blank=True)),
                ('source', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('facility', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='organizations.facility')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='organizations.organization')),
                ('reporting_period', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='submissions.reportingperiod')),
            ],
            options={'db_table': 'dashboard_compliancesnapshot'},
        ),
    ]
