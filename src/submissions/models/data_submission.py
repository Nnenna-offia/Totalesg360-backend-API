from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

from common.models import BaseModel


class DataSubmission(BaseModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        APPROVED = "APPROVED", "Approved"

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    indicator = models.ForeignKey(
        "indicators.Indicator",
        on_delete=models.PROTECT,
        related_name="submissions",
    )
    reporting_period = models.ForeignKey(
        "submissions.ReportingPeriod",
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    facility = models.ForeignKey(
        "organizations.Facility",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="submissions",
    )

    # Value fields (only one should be used depending on indicator.data_type)
    value_number = models.FloatField(null=True, blank=True)
    value_text = models.TextField(null=True, blank=True)
    value_boolean = models.BooleanField(null=True, blank=True)

    metadata = models.JSONField(default=dict, blank=True)

    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT, db_index=True)

    submitted_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="submissions_made",
    )
    submitted_at = models.DateTimeField(null=True, blank=True)

    approved_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="submissions_approved",
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "submissions_datasubmission"
        app_label = "submissions"
        unique_together = (("organization", "indicator", "reporting_period", "facility"),)
        indexes = [
            models.Index(fields=["organization", "reporting_period"], name="submissions__org_period_idx"),
            models.Index(fields=["indicator"], name="submissions__indicator_idx"),
            models.Index(fields=["status"], name="submissions__status_idx"),
        ]

    def clean(self):
        # Ensure only one value field is populated
        values = [self.value_number is not None, self.value_text not in (None, ""), self.value_boolean is not None]
        if sum(1 for v in values if v) > 1:
            raise ValidationError("Only one of value_number, value_text, value_boolean may be set")

    def mark_submitted(self, by_user):
        self.status = self.Status.SUBMITTED
        self.submitted_by = by_user
        self.submitted_at = timezone.now()
        self.save(update_fields=["status", "submitted_by", "submitted_at", "updated_at"])

    def mark_approved(self, by_user):
        self.status = self.Status.APPROVED
        self.approved_by = by_user
        self.approved_at = timezone.now()
        self.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])

    def __str__(self):
        return f"{self.organization} • {self.indicator.code} • {self.reporting_period}"
