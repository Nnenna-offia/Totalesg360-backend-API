from django.db import models
from common.models import BaseModel

from activities.models.scope import Scope


class ActivityType(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=50)
    scope = models.ForeignKey(Scope, on_delete=models.PROTECT, related_name='activity_types')
    is_active = models.BooleanField(default=True)
    # Controls ordering in UI lists
    display_order = models.IntegerField(default=0, db_index=True)

    class DataType(models.TextChoices):
        NUMBER = "number", "Number"
        PERCENTAGE = "percentage", "Percentage"
        BOOLEAN = "boolean", "Boolean"
        TEXT = "text", "Text"
        COUNT = "count", "Count"

    # Defines the input type expected for this activity
    data_type = models.CharField(max_length=20, choices=DataType.choices, default=DataType.NUMBER, db_index=True)

    # Whether evidence (file upload) is required when submitting
    requires_evidence = models.BooleanField(default=False)

    # Whether submission of this activity is mandatory
    is_required = models.BooleanField(default=False, db_index=True)
    
    # Link to indicator: activities generate indicator values
    indicator = models.ForeignKey(
        "indicators.Indicator",
        on_delete=models.PROTECT,
        related_name="activity_types",
        help_text="The indicator that this activity type contributes to"
    )

    def save(self, *args, **kwargs):
        # Auto-sync unit from linked indicator for consistency.
        # If indicator is set, prefer its canonical unit.
        if getattr(self, "indicator", None):
            indicator_unit = getattr(self.indicator, "unit", None)
            if indicator_unit:
                self.unit = indicator_unit
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'activities_activitytype'
        verbose_name = 'Activity Type'
        verbose_name_plural = 'Activity Types'

    def __str__(self):
        return f"{self.name} ({self.unit})"
