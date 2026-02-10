from django.db import models
from common.models import BaseModel
from .organization import Organization


class Facility(BaseModel):
    """
    Represents a physical site/branch/plant within an organization.
    Data submissions can be scoped to a facility.
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="facilities",
    )
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True)
    facility_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="e.g., Plant, Branch, Office, Refinery"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional facility-specific data"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'organizations_facility'
        verbose_name = 'Facility'
        verbose_name_plural = 'Facilities'
        unique_together = [('organization', 'name')]
        indexes = [
            models.Index(fields=['organization', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.organization.name})"