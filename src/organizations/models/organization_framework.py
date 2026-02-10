"""Organization-Framework relationship with audit tracking."""
from django.db import models
from common.models import BaseModel
from .organization import Organization
from .regulatory_framework import RegulatoryFramework


class OrganizationFramework(BaseModel):
    """Links organizations to regulatory frameworks with audit tracking.
    
    Supports:
    - Multiple frameworks per organization
    - Primary/default framework designation
    - Enable/disable behavior
    - Audit trail of framework assignments
    """
    
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="framework_assignments"
    )
    framework = models.ForeignKey(
        RegulatoryFramework,
        on_delete=models.PROTECT,
        related_name="organization_assignments"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Whether this is the organization's primary reporting framework"
    )
    is_enabled = models.BooleanField(
        default=True,
        help_text="Whether framework is actively used"
    )
    assigned_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When framework was assigned to organization"
    )
    assigned_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="framework_assignments_made",
        help_text="User who assigned this framework (null for system assignments)"
    )
    
    class Meta:
        db_table = "organizations_organization_framework"
        verbose_name = "Organization Framework"
        verbose_name_plural = "Organization Frameworks"
        unique_together = [("organization", "framework")]
        ordering = ["-is_primary", "-framework__priority", "framework__name"]
        indexes = [
            models.Index(fields=["organization", "is_enabled"]),
            models.Index(fields=["framework", "is_enabled"]),
        ]
    
    def __str__(self):
        primary = " [PRIMARY]" if self.is_primary else ""
        return f"{self.organization.name} → {self.framework.code}{primary}"
