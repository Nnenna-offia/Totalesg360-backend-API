"""Framework Requirement model for mapping ESG indicators to compliance requirements."""
from django.db import models
from common.models import BaseModel
from organizations.models import RegulatoryFramework


class FrameworkRequirement(BaseModel):
    """
    Requirement within a regulatory framework.
    
    Examples:
    - GRI 305-1: Direct GHG Emissions
    - IFRS S2-1: Physical Climate Risks
    - SASB EM-EP-110a: Air Quality Metrics
    - TCFD: Governance Structure
    - NGX: Environmental & Social Report
    
    Each requirement is associated with a framework and pillar (E/S/G).
    """
    
    class Pillar(models.TextChoices):
        ENVIRONMENTAL = "ENV", "Environmental"
        SOCIAL = "SOC", "Social"
        GOVERNANCE = "GOV", "Governance"
    
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        DEPRECATED = "deprecated", "Deprecated"
        ARCHIVED = "archived", "Archived"
    
    framework = models.ForeignKey(
        RegulatoryFramework,
        on_delete=models.CASCADE,
        related_name="requirements",
        help_text="The framework this requirement belongs to"
    )
    
    code = models.CharField(
        max_length=100,
        help_text="Unique identifier within framework (e.g., GRI 305-1, IFRS S2-1)"
    )
    
    title = models.CharField(
        max_length=255,
        help_text="Short title of the requirement"
    )
    
    description = models.TextField(
        blank=True,
        help_text="Detailed description of what's required"
    )
    
    pillar = models.CharField(
        max_length=20,
        choices=Pillar.choices,
        help_text="ESG pillar this requirement addresses"
    )
    
    is_mandatory = models.BooleanField(
        default=True,
        help_text="Whether this is a mandatory or recommended requirement"
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
        help_text="Status of the requirement (active/deprecated/archived)"
    )
    
    # Additional metadata
    priority = models.IntegerField(
        default=0,
        help_text="Priority level for display/sorting (higher = more important)"
    )
    
    guidance_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Link to framework documentation or guidance"
    )
    
    version = models.CharField(
        max_length=50,
        blank=True,
        help_text="Version of requirement (e.g., 2023, v2.0)"
    )
    
    class Meta:
        db_table = "compliance_framework_requirement"
        verbose_name = "Framework Requirement"
        verbose_name_plural = "Framework Requirements"
        unique_together = [("framework", "code")]
        ordering = ["framework__priority", "pillar", "code"]
        indexes = [
            models.Index(fields=["framework", "pillar"]),
            models.Index(fields=["framework", "status"]),
            models.Index(fields=["pillar", "status"]),
        ]
    
    def __str__(self):
        return f"{self.framework.code} - {self.code}: {self.title}"
    
    def __repr__(self):
        return f"<FrameworkRequirement {self.framework.code}/{self.code}>"
