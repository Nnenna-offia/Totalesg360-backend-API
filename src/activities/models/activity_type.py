from django.db import models
from common.models import BaseModel

from activities.models.scope import Scope


class ActivityType(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=50)
    scope = models.ForeignKey(Scope, on_delete=models.PROTECT, related_name='activity_types')
    category = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Link to indicator: activities generate indicator values
    indicator = models.ForeignKey(
        "indicators.Indicator",
        on_delete=models.PROTECT,
        related_name="activity_types",
        null=True,
        blank=True,
        help_text="The indicator that this activity type contributes to"
    )

    class Meta:
        db_table = 'activities_activitytype'
        verbose_name = 'Activity Type'
        verbose_name_plural = 'Activity Types'

    def __str__(self):
        return f"{self.name} ({self.unit})"
