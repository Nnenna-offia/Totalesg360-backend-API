from django.db import models
from django.conf import settings
from common.models import BaseModel


class TargetGoal(BaseModel):
    class Direction(models.TextChoices):
        INCREASE = 'increase', 'Increase'
        DECREASE = 'decrease', 'Decrease'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        ARCHIVED = 'archived', 'Archived'

    class ReportingFrequency(models.TextChoices):
        DAILY = "DAILY", "Daily"
        WEEKLY = "WEEKLY", "Weekly"
        BI_WEEKLY = "BI_WEEKLY", "Bi-Weekly"
        MONTHLY = "MONTHLY", "Monthly"
        QUARTERLY = "QUARTERLY", "Quarterly"
        SEMI_ANNUAL = "SEMI_ANNUAL", "Semi-Annual"
        ANNUAL = "ANNUAL", "Annual"

    organization = models.ForeignKey(
        'organizations.Organization', on_delete=models.CASCADE, related_name='target_goals'
    )
    indicator = models.ForeignKey(
        'indicators.Indicator', on_delete=models.PROTECT, related_name='target_goals'
    )
    facility = models.ForeignKey(
        'organizations.Facility', null=True, blank=True, on_delete=models.SET_NULL, related_name='target_goals'
    )

    department = models.ForeignKey(
        'organizations.Department', null=True, blank=True, on_delete=models.SET_NULL, related_name='target_goals',
        help_text="Department responsible for this target (optional)"
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    reporting_frequency = models.CharField(
        max_length=20,
        choices=ReportingFrequency.choices,
        default=ReportingFrequency.ANNUAL,
        db_index=True,
        help_text="Reporting frequency for this target (DAILY, WEEKLY, BI_WEEKLY, MONTHLY, QUARTERLY, SEMI_ANNUAL, ANNUAL)"
    )

    baseline_year = models.IntegerField()
    baseline_value = models.FloatField()

    target_year = models.IntegerField()
    target_value = models.FloatField()

    direction = models.CharField(max_length=16, choices=Direction.choices, default=Direction.DECREASE)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE, db_index=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='created_targets')

    class Meta:
        db_table = 'targets_targetgoal'
        verbose_name = 'Target Goal'
        verbose_name_plural = 'Target Goals'
        indexes = [models.Index(fields=['organization', 'status'])]

    def __str__(self):
        return f"{self.organization} • {self.name} ({self.indicator.code})"
