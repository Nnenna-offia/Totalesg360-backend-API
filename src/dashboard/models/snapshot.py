from django.db import models
from django.utils import timezone

from common.models import BaseModel


class SnapshotBase(BaseModel):
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, related_name='%(class)s_snapshots')
    facility = models.ForeignKey('organizations.Facility', null=True, blank=True, on_delete=models.SET_NULL)
    reporting_period = models.ForeignKey('submissions.ReportingPeriod', null=True, blank=True, on_delete=models.SET_NULL)
    snapshot_date = models.DateTimeField(default=timezone.now, db_index=True)
    data = models.JSONField(default=dict, blank=True)
    source = models.CharField(max_length=255, blank=True, help_text='Source or reason for snapshot (e.g., nightly_job, manual)')
    created_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        abstract = True


class DashboardSnapshot(SnapshotBase):
    """Precomputed dashboard summary (E/S/G subscores, trends, metadata)."""
    class Meta:
        db_table = 'dashboard_dashboardsnapshot'
        verbose_name = 'Dashboard Snapshot'
        indexes = [
            models.Index(fields=['snapshot_date']),
            models.Index(fields=['organization', 'snapshot_date']),
            models.Index(fields=['facility']),
        ]


class DashboardMetric(models.Model):
    """Normalized ESG metric per organization & reporting period for fast reads."""
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE)
    reporting_period = models.ForeignKey('submissions.ReportingPeriod', null=True, blank=True, on_delete=models.SET_NULL)
    pillar = models.CharField(max_length=8, blank=True, null=True)

    environmental_score = models.FloatField(null=True, blank=True)
    social_score = models.FloatField(null=True, blank=True)
    governance_score = models.FloatField(null=True, blank=True)
    overall_esg_score = models.FloatField(null=True, blank=True)

    calculated_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'dashboard_dashboardmetric'
        indexes = [models.Index(fields=['organization', 'reporting_period']), models.Index(fields=['calculated_at'])]


class TargetSnapshot(SnapshotBase):
    """Precomputed snapshot of targets and progress for fast lookup."""

    class Meta:
        db_table = 'dashboard_targetsnapshot'
        verbose_name = 'Target Snapshot'
        indexes = [
            models.Index(fields=['snapshot_date']),
            models.Index(fields=['organization', 'snapshot_date']),
            models.Index(fields=['facility']),
        ]


class EmissionSnapshot(SnapshotBase):
    """Precomputed emission aggregates (by scope, facility, period)."""

    class Meta:
        db_table = 'dashboard_emissionsnapshot'
        verbose_name = 'Emission Snapshot'
        indexes = [
            models.Index(fields=['snapshot_date']),
            models.Index(fields=['organization', 'snapshot_date']),
            models.Index(fields=['facility']),
        ]


class IndicatorSnapshot(SnapshotBase):
    """Precomputed indicator aggregates and trends used by charts."""

    class Meta:
        db_table = 'dashboard_indicatorsnapshot'
        verbose_name = 'Indicator Snapshot'
        indexes = [
            models.Index(fields=['snapshot_date']),
            models.Index(fields=['organization', 'snapshot_date']),
            models.Index(fields=['facility']),
        ]



class ComplianceSnapshot(SnapshotBase):
    """Precomputed compliance and framework completion status."""

    class Meta:
        db_table = 'dashboard_compliancesnapshot'
        verbose_name = 'Compliance Snapshot'
        indexes = [
            models.Index(fields=['snapshot_date']),
            models.Index(fields=['organization', 'snapshot_date']),
            models.Index(fields=['facility']),
        ]
