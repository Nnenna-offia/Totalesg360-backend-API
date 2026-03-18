"""Department model for organizational structure."""
from django.db import models
from common.models import BaseModel
from .organization import Organization


class Department(BaseModel):
    """
    Represents a department/division within an organization.
    """
    
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="departments",
        help_text="Organization this department belongs to"
    )
    
    name = models.CharField(
        max_length=255,
        help_text="Department name"
    )
    
    code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Department code/abbreviation"
    )
    
    description = models.TextField(
        blank=True,
        help_text="Department description"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether department is active"
    )
    
    class Meta:
        db_table = "organizations_department"
        verbose_name = "Department"
        verbose_name_plural = "Departments"
        unique_together = [["organization", "name"]]
        indexes = [
            models.Index(fields=["organization", "is_active"]),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.organization.name})"
