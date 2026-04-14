"""Compliance Gap Priority model - prioritizes which framework requirements need attention."""
from django.db import models
from common.models import BaseModel
from organizations.models import Organization, RegulatoryFramework
from .framework_requirement import FrameworkRequirement


class ComplianceGapPriority(BaseModel):
    """
    Prioritized view of compliance gaps for an organization-framework pair.
    
    Calculates priority based on:
    - Mandatory requirement (weight: 40%)
    - Framework priority (weight: 30%)
    - Pillar importance (weight: 20%)
    - Existing indicator coverage impact (weight: 10%)
    
    Priority Score = weighted combination of factors (0-100)
    
    Example:
    - Mandatory GRI 305-1 (CO2) = High Priority
    - Optional GRI 408-1 (Child Labor) = Lower Priority (but mandatory=True changes this)
    """
    
    class PriorityLevel(models.TextChoices):
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"
    
    class ImpactCategory(models.TextChoices):
        DIRECT = "direct", "Direct Impact"
        INDIRECT = "indirect", "Indirect Impact"
        STRATEGIC = "strategic", "Strategic"
    
    # Relationships
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="compliance_gaps",
        db_index=True,
        help_text="Organization with compliance gap"
    )
    
    framework = models.ForeignKey(
        RegulatoryFramework,
        on_delete=models.CASCADE,
        related_name="prioritized_gaps",
        db_index=True,
        help_text="Framework containing the requirement"
    )
    
    requirement = models.ForeignKey(
        FrameworkRequirement,
        on_delete=models.CASCADE,
        related_name="compliance_gaps",
        help_text="Uncovered framework requirement"
    )
    
    # Priority Calculation Components
    mandatory_weight = models.FloatField(
        default=0.0,
        help_text="Weight from mandatory requirement (0-40)"
    )
    
    framework_weight = models.FloatField(
        default=0.0,
        help_text="Weight from framework priority (0-30)"
    )
    
    pillar_weight = models.FloatField(
        default=0.0,
        help_text="Weight from pillar importance (0-20)"
    )
    
    coverage_impact_weight = models.FloatField(
        default=0.0,
        help_text="Weight from coverage impact (0-10)"
    )
    
    # Overall Priority
    priority_score = models.FloatField(
        default=0.0,
        validators=[],
        help_text="Total priority score (0-100)"
    )
    
    priority_level = models.CharField(
        max_length=20,
        choices=PriorityLevel.choices,
        db_index=True,
        help_text="High/Medium/Low priority"
    )
    
    impact_category = models.CharField(
        max_length=20,
        choices=ImpactCategory.choices,
        default=ImpactCategory.DIRECT,
        help_text="Type of impact if not addressed"
    )
    
    # Gap Context
    gap_description = models.TextField(
        blank=True,
        help_text="Why this requirement is not covered"
    )
    
    efforts_to_close = models.CharField(
        max_length=255,
        blank=True,
        help_text="What's needed to close this gap"
    )
    
    estimated_effort_days = models.IntegerField(
        default=0,
        help_text="Estimated effort to address gap (days)"
    )
    
    # Tracking
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this gap should be actively monitored"
    )
    
    last_assessed_at = models.DateTimeField(
        auto_now=True,
        help_text="When this gap priority was last calculated"
    )
    
    class Meta:
        db_table = "compliance_gap_priority"
        verbose_name = "Compliance Gap Priority"
        verbose_name_plural = "Compliance Gap Priorities"
        unique_together = [("organization", "framework", "requirement")]
        ordering = ["-priority_score", "priority_level", "framework__priority"]
        indexes = [
            models.Index(fields=["organization", "priority_level"]),
            models.Index(fields=["framework", "priority_level"]),
            models.Index(fields=["is_active", "priority_score"]),
            models.Index(fields=["organization", "framework", "priority_level"]),
        ]
    
    def __str__(self):
        return f"{self.organization.name} - {self.requirement.code}: {self.priority_level} (Score: {self.priority_score})"
    
    def __repr__(self):
        return f"<ComplianceGapPriority {self.framework.code}/{self.requirement.code} {self.priority_score}>"
    
    def is_critical(self) -> bool:
        """Returns True if this is a high-priority mandatory requirement."""
        return self.priority_level == self.PriorityLevel.HIGH and self.requirement.is_mandatory
    
    def get_effort_estimate_text(self) -> str:
        """Returns human-readable effort estimate."""
        if self.estimated_effort_days == 0:
            return "Unknown"
        elif self.estimated_effort_days <= 1:
            return "Less than a day"
        elif self.estimated_effort_days <= 5:
            return f"{self.estimated_effort_days} days"
        elif self.estimated_effort_days <= 20:
            return f"{self.estimated_effort_days // 5} weeks"
        else:
            return f"{self.estimated_effort_days // 20} months"
