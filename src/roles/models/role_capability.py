# roles/models/role_capability.py

from django.db import models
from common.models import BaseModel


class RoleCapability(BaseModel):
    """
    Maps Roles to Capabilities (M2M junction table with extra fields).
    """
    role = models.ForeignKey(
        'roles.Role',
        on_delete=models.CASCADE,
        related_name="role_capabilities"
    )
    capability = models.ForeignKey(
        'roles.Capability',
        on_delete=models.CASCADE,
        related_name="role_capabilities"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'roles_role_capability'
        verbose_name = 'Role Capability'
        verbose_name_plural = 'Role Capabilities'
        unique_together = [('role', 'capability')]
        indexes = [
            models.Index(fields=['role', 'is_active']),
            models.Index(fields=['capability', 'is_active']),
        ]

    def __str__(self):
        return f"{self.role.code} → {self.capability.code}"

