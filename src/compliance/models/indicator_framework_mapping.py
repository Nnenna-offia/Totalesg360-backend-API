"""Indicator-Framework mapping model connecting indicators to compliance requirements."""
from django.db import models
from common.models import BaseModel
from indicators.models import Indicator
from organizations.models import RegulatoryFramework
from .framework_requirement import FrameworkRequirement


class IndicatorFrameworkMapping(BaseModel):
    """
    Maps indicators to framework requirements.
    
    One indicator can map to multiple frameworks/requirements.
    One requirement can be addressed by multiple indicators.
    
    Example:
    - Indicator: "Scope 1 Emissions"
      Maps to:
      - GRI 305-1: Direct GHG Emissions
      - IFRS S2-1: Physical Risks
      - SASB EM-EP-110a: Air Quality
    
    This enables:
    - Compliance gap analysis
    - Framework alignment reports
    - Multi-framework reporting
    - Requirement coverage analysis
    """
    
    class MappingType(models.TextChoices):
        PRIMARY = "primary", "Primary"  # Core requirement satisfaction
        SUPPORTING = "supporting", "Supporting"  # Partial/contributing satisfaction
        REFERENCE = "reference", "Reference"  # Informational/contextual
    
    indicator = models.ForeignKey(
        Indicator,
        on_delete=models.CASCADE,
        related_name="regulatory_requirement_mappings",
        help_text="The indicator being mapped"
    )
    
    framework = models.ForeignKey(
        RegulatoryFramework,
        on_delete=models.CASCADE,
        related_name="indicator_mappings",
        help_text="The framework this mapping relates to"
    )
    
    requirement = models.ForeignKey(
        FrameworkRequirement,
        on_delete=models.CASCADE,
        related_name="indicator_mappings",
        help_text="The specific requirement being addressed"
    )
    
    mapping_type = models.CharField(
        max_length=20,
        choices=MappingType.choices,
        default=MappingType.PRIMARY,
        help_text="Type of mapping (primary/supporting/reference)"
    )
    
    is_primary = models.BooleanField(
        default=False,
        help_text="Whether this is the primary indicator for this requirement"
    )
    
    # Mapping justification
    rationale = models.TextField(
        blank=True,
        help_text="Explanation of how indicator satisfies/addresses requirement"
    )
    
    coverage_percent = models.IntegerField(
        default=100,
        help_text="How much of the requirement is covered by this indicator (0-100%)"
    )
    
    # Status tracking
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this mapping is active/current"
    )
    
    # Optional metadata
    notes = models.TextField(
        blank=True,
        help_text="Additional notes on this mapping"
    )
    
    class Meta:
        db_table = "compliance_indicator_framework_mapping"
        verbose_name = "Indicator Framework Mapping"
        verbose_name_plural = "Indicator Framework Mappings"
        unique_together = [("indicator", "framework", "requirement")]
        ordering = ["-is_primary", "-mapping_type", "-coverage_percent"]
        indexes = [
            models.Index(fields=["indicator", "framework"]),
            models.Index(fields=["framework", "is_active"]),
            models.Index(fields=["requirement", "is_active"]),
            models.Index(fields=["indicator", "is_active"]),
        ]
    
    def __str__(self):
        return f"{self.indicator.code} ← {self.requirement.code} ({self.framework.code})"
    
    def __repr__(self):
        return f"<IndicatorFrameworkMapping {self.indicator.code}/{self.requirement.code}>"
    
    def get_coverage_status(self):
        """Status of requirement coverage by this indicator."""
        if self.coverage_percent >= 100:
            return "full"
        elif self.coverage_percent >= 75:
            return "substantial"
        elif self.coverage_percent >= 50:
            return "partial"
        else:
            return "minimal"
