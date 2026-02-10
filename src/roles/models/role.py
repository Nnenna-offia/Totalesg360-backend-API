# roles/models/role.py

from django.db import models
from common.models import BaseModel


class Role(BaseModel):
    """
    Represents a role within an organization (e.g., org_admin, data_manager).
    Roles are mapped to Capabilities.
    """
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique identifier (e.g., org_admin, environmental_officer)"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_system = models.BooleanField(
        default=False,
        help_text="System roles cannot be deleted"
    )

    class Meta:
        db_table = 'roles_role'
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'
        ordering = ['name']

    def __str__(self):
        return self.name or self.code
