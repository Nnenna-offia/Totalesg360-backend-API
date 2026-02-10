# roles/models/capability.py

from django.db import models
from common.models import BaseModel


class Capability(BaseModel):
    """
    Represents a fine-grained permission (e.g., report.submit, org.manage).
    """
    code = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique capability code (e.g., manage_organization, submit_environmental)"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'roles_capability'
        verbose_name = 'Capability'
        verbose_name_plural = 'Capabilities'
        ordering = ['name']

    def __str__(self):
        return self.name or self.code
