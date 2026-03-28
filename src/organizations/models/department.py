"""Department model for organizational structure."""
from django.db import models
from django.conf import settings
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

    head = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="departments_led",
        help_text="Head of department (optional)"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether department is active"
    )
    
    class Meta:
        db_table = "organizations_department"
        app_label = "organizations"
        verbose_name = "Department"
        verbose_name_plural = "Departments"
        unique_together = [["organization", "name"]]
        indexes = [
            models.Index(fields=["organization", "is_active"]),
            models.Index(fields=["organization"]),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.organization.name})"
