"""Framework Readiness model - tracks compliance readiness for each organization-framework pair."""
from django.db import models
from common.models import BaseModel
from organizations.models import Organization, RegulatoryFramework
from submissions.models import ReportingPeriod


class FrameworkReadiness(BaseModel):
    """
    Tracks framework compliance readiness for an organization.
    
    Readiness Score = (Mandatory Coverage * 0.7) + (Optional Coverage * 0.3)
    
    This score answers: "How ready is this organization for this framework?"
    
    Risk Level Mapping:
    - Low: Readiness >= 80%
    - Medium: Readiness >= 50% and < 80%
    - High: Readiness < 50%
    """
    
    class RiskLevel(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
    
    # Relationships
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="framework_readiness",
        db_index=True,
        help_text="Organization being assessed"
    )
    
    framework = models.ForeignKey(
        RegulatoryFramework,
        on_delete=models.CASCADE,
        related_name="readiness_scores",
        db_index=True,
        help_text="Framework for assessment"
    )
    
    reporting_period = models.ForeignKey(
        ReportingPeriod,
        on_delete=models.CASCADE,
        related_name="framework_readiness",
        db_index=True,
        help_text="Reporting period for this assessment"
    )
    
    # Coverage Metrics
    total_requirements = models.IntegerField(
        default=0,
        help_text="Total requirements in framework"
    )
    
    covered_requirements = models.IntegerField(
        default=0,
        help_text="Requirements with at least one indicator mapped"
    )
    
    coverage_percent = models.FloatField(
        default=0.0,
        validators=[],
        help_text="Overall coverage percentage (0-100%)"
    )
    
    mandatory_requirements = models.IntegerField(
        default=0,
        help_text="Total mandatory requirements"
    )
    
    mandatory_covered = models.IntegerField(
        default=0,
        help_text="Mandatory requirements with coverage"
    )
    
    mandatory_coverage_percent = models.FloatField(
        default=0.0,
        validators=[],
        help_text="Mandatory requirement coverage (0-100%)"
    )
    
    # Readiness Calculation
    readiness_score = models.FloatField(
        default=0.0,
        validators=[],
        help_text="Weighted readiness score: (mandatory * 0.7) + (optional * 0.3)"
    )
    
    risk_level = models.CharField(
        max_length=20,
        choices=RiskLevel.choices,
        default=RiskLevel.MEDIUM,
        db_index=True,
        help_text="Compliance risk level based on readiness"
    )
    
    # Metadata
    is_current = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this is the current readiness assessment"
    )
    
    calculated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this assessment was last calculated"
    )
    
    class Meta:
        db_table = "compliance_framework_readiness"
        verbose_name = "Framework Readiness"
        verbose_name_plural = "Framework Readiness Scores"
        unique_together = [("organization", "framework", "reporting_period")]
        ordering = ["-calculated_at", "framework__priority"]
        indexes = [
            models.Index(fields=["organization", "framework"]),
            models.Index(fields=["organization", "risk_level"]),
            models.Index(fields=["framework", "risk_level"]),
            models.Index(fields=["is_current", "risk_level"]),
        ]
    
    def __str__(self):
        return f"{self.organization.name} - {self.framework.code}: {self.readiness_score}% (Risk: {self.get_risk_level_display()})"
    
    def __repr__(self):
        return f"<FrameworkReadiness {self.organization.code}/{self.framework.code} {self.readiness_score}%>"
    
    def is_on_track(self) -> bool:
        """Returns True if readiness score is >= 80%."""
        return self.readiness_score >= 80
    
    def is_at_risk(self) -> bool:
        """Returns True if readiness score is between 50%-80%."""
        return 50 <= self.readiness_score < 80
    
    def is_critical(self) -> bool:
        """Returns True if readiness score is < 50%."""
        return self.readiness_score < 50
    
    def get_uncovered_count(self) -> int:
        """Returns number of uncovered requirements."""
        return self.total_requirements - self.covered_requirements
    
    def get_mandatory_gap_count(self) -> int:
        """Returns number of uncovered mandatory requirements."""
        return self.mandatory_requirements - self.mandatory_covered
