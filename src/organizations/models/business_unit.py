from django.db import models
from common.models import BaseModel
from .organization import Organization


class BusinessUnit(BaseModel):
    """Represents a business unit within an organization."""

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="business_units",
        help_text="Organization this business unit belongs to",
    )

    name = models.CharField(max_length=255, help_text="Business unit name")

    class Meta:
        db_table = "organizations_businessunit"
        verbose_name = "Business Unit"
        verbose_name_plural = "Business Units"
        unique_together = [["organization", "name"]]

    def __str__(self):
        return f"{self.name} ({self.organization.name})"
