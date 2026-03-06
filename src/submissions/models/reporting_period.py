from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

from common.models import BaseModel


class ReportingPeriod(BaseModel):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        LOCKED = "LOCKED", "Locked"
        SUBMITTED = "SUBMITTED", "Submitted"

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="reporting_periods",
    )
    year = models.IntegerField(db_index=True)
    quarter = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN, db_index=True)
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
        unique_together = (("organization", "year", "quarter"),)
        indexes = [models.Index(fields=["organization", "status"])]

    def clean(self):
        # Ensure quarter is between 1 and 4 if provided
        if self.quarter is not None and not (1 <= self.quarter <= 4):
            raise ValidationError("quarter must be between 1 and 4")

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
        q = f"Q{self.quarter}" if self.quarter else ""
        return f"{self.organization} - {self.year} {q} ({self.get_status_display()})"
