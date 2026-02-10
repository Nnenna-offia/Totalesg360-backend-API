"""Regulatory framework model for compliance and reporting."""
from django.db import models
from common.models import BaseModel


class RegulatoryFramework(BaseModel):
    """System-defined regulatory frameworks and standards.
    
    Represents compliance frameworks like NESREA, CBN, GRI, ISSB, etc.
    Admin-configurable, not user-created.
    """
    
    class Jurisdiction(models.TextChoices):
        NIGERIA = "NIGERIA", "Nigeria"
        INTERNATIONAL = "INTERNATIONAL", "International"
    
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique identifier (e.g., NESREA, GRI, ISSB)"
    )
    name = models.CharField(
        max_length=200,
        help_text="Full framework name"
    )
    jurisdiction = models.CharField(
        max_length=20,
        choices=Jurisdiction.choices,
        help_text="Regulatory jurisdiction"
    )
    description = models.TextField(
        blank=True,
        help_text="Framework description and purpose"
    )
    sector = models.CharField(
        max_length=50,
        blank=True,
        help_text="Sector-specific framework (empty for cross-sector)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether framework is available for selection"
    )
    priority = models.IntegerField(
        default=0,
        help_text="Display/assignment priority (higher = more important)"
    )
    
    class Meta:
        db_table = "organizations_regulatory_framework"
        verbose_name = "Regulatory Framework"
        verbose_name_plural = "Regulatory Frameworks"
        ordering = ["-priority", "name"]
        indexes = [
            models.Index(fields=["jurisdiction", "is_active"]),
            models.Index(fields=["sector", "is_active"]),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_jurisdiction_display()})"
