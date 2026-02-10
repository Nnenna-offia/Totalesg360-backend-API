# organizations/models/membership.py
from django.db import models
from common.models import BaseModel
from .organization import Organization
from .facility import Facility


class Membership(BaseModel):
    """
    Joins User to Organization with a Role.
    Optionally scoped to a Facility and/or pillar/reporting period.
    Tracks who added the member for audit.
    """
    user = models.ForeignKey(
        'accounts.User',  # Use string reference to avoid circular import
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.ForeignKey(
        'roles.Role',  # Use string reference
        on_delete=models.PROTECT,
        related_name="memberships",
    )
    facility = models.ForeignKey(
        Facility,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="memberships",
        help_text="Optional: scope membership to a specific facility"
    )
    
    # Optional: scope to specific pillars or reporting periods
    scope = models.JSONField(
        default=dict,
        blank=True,
        help_text="Optional contextual constraints (pillar, period, etc.)"
    )
    
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    # Audit: who added this member
    added_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="memberships_granted",
    )

    class Meta:
        db_table = 'organizations_membership'
        verbose_name = 'Membership'
        verbose_name_plural = 'Memberships'
        unique_together = [('user', 'organization', 'role')]
        indexes = [
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.organization.name} ({self.role.name})"
