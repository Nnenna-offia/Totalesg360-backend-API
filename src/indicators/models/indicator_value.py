from django.db import models
from common.models import BaseModel


class IndicatorValue(BaseModel):
    """Stores calculated/aggregated indicator values derived from activities.
    
    This model stores the result of aggregating activity submissions for
    activity-based indicators. Values are recalculated whenever underlying
    activities change.
    """
    
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="indicator_values",
    )
    indicator = models.ForeignKey(
        "indicators.Indicator",
        on_delete=models.CASCADE,
        related_name="calculated_values",
    )
    reporting_period = models.ForeignKey(
        "submissions.ReportingPeriod",
        on_delete=models.CASCADE,
        related_name="indicator_values",
    )
    facility = models.ForeignKey(
        "organizations.Facility",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="indicator_values",
    )
    
    value = models.FloatField(help_text="Aggregated value from activities")
    
    # Metadata about the calculation
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional calculation metadata (activity count, last update, etc.)"
    )

    class Meta:
        db_table = "indicators_indicatorvalue"
        verbose_name = "Indicator Value"
        verbose_name_plural = "Indicator Values"
        unique_together = (("organization", "indicator", "reporting_period", "facility"),)
        indexes = [
            models.Index(fields=["organization", "reporting_period"], name="indval__org_period_idx"),
            models.Index(fields=["indicator"], name="indval__indicator_idx"),
        ]

    def __str__(self):
        return f"{self.organization} • {self.indicator.code} • {self.reporting_period} = {self.value}"
