from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

from common.models import BaseModel


class ReportingPeriod(BaseModel):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        LOCKED = "LOCKED", "Locked"
        SUBMITTED = "SUBMITTED", "Submitted"

    class PeriodType(models.TextChoices):
        DAILY = "DAILY", "Daily"
        WEEKLY = "WEEKLY", "Weekly"
        BI_WEEKLY = "BI_WEEKLY", "Bi-Weekly"
        MONTHLY = "MONTHLY", "Monthly"
        QUARTERLY = "QUARTERLY", "Quarterly"
        SEMI_ANNUAL = "SEMI_ANNUAL", "Semi-Annual"
        ANNUAL = "ANNUAL", "Annual"
        CUSTOM = "CUSTOM", "Custom"

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="reporting_periods",
    )

    name = models.CharField(
        max_length=120,
        help_text="Human readable label e.g. Week 1 2025, Jan 2025, Q1 2025"
    )

    period_type = models.CharField(
        max_length=20,
        choices=PeriodType.choices,
        db_index=True
    )

    start_date = models.DateField()

    end_date = models.DateField()

    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.OPEN,
        db_index=True
    )

    opened_at = models.DateTimeField(default=timezone.now)

    locked_at = models.DateTimeField(null=True, blank=True)

    locked_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="periods_locked",
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "submissions_reportingperiod"
        app_label = "submissions"
        unique_together = [("organization", "name")]
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["organization", "period_type"]),
            models.Index(fields=["start_date", "end_date"]),
        ]

    def clean(self):
        # Validate start_date is before end_date
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError("Start date must be before end date")

        # Check for overlapping periods
        if self.organization and self.start_date and self.end_date:
            overlapping = ReportingPeriod.objects.filter(
                organization=self.organization,
                start_date__lte=self.end_date,
                end_date__gte=self.start_date
            ).exclude(id=self.id)

            if overlapping.exists():
                raise ValidationError("Reporting period overlaps with existing period")

    def can_edit(self):
        return self.status == self.Status.OPEN

    def lock(self, *, by_user=None):
        if self.status == self.Status.LOCKED:
            return
        self.status = self.Status.LOCKED
        self.locked_at = timezone.now()
        self.locked_by = by_user
        self.save(update_fields=["status", "locked_at", "locked_by", "updated_at"])

    def delete(self, *args, **kwargs):
        # Prevent deletion if DataSubmission rows exist for this period
        try:
            from submissions.models import DataSubmission  # type: ignore
        except Exception:
            DataSubmission = None

        if DataSubmission is not None and DataSubmission.objects.filter(reporting_period=self).exists():
            raise ValidationError("Cannot delete ReportingPeriod with existing submissions")
        return super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.organization} - {self.name} ({self.get_status_display()})"
