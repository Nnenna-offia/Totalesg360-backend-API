"""Pillar Score model - aggregated scores for ESG pillars (Environmental, Social, Governance)."""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from common.models import BaseModel
from organizations.models import Organization
from submissions.models import ReportingPeriod


class PillarScore(BaseModel):
    """
    Stores aggregated scores for ESG pillars (Environmental, Social, Governance).
    
    Pillar Score = Average of all Indicator Scores under that pillar.
    
    Score Hierarchy:
    Indicator Scores → Pillar Scores → Organization ESG Score
    """
    
    class PillarType(models.TextChoices):
        ENVIRONMENTAL = "ENV", "Environmental"
        SOCIAL = "SOC", "Social"
        GOVERNANCE = "GOV", "Governance"
    
    # Relationships
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="pillar_scores",
        db_index=True,
        help_text="Organization being scored"
    )
    
    reporting_period = models.ForeignKey(
        ReportingPeriod,
        on_delete=models.CASCADE,
        related_name="pillar_scores",
        db_index=True,
        help_text="Reporting period for this score"
    )
    
    # Pillar Data
    pillar = models.CharField(
        max_length=8,
        choices=PillarType.choices,
        db_index=True,
        help_text="ESG Pillar: Environmental (ENV), Social (SOC), or Governance (GOV)"
    )
    
    score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Aggregated pillar score (0-100)"
    )
    
    # Calculation Details
    indicator_count = models.IntegerField(
        help_text="Number of indicators included in this pillar score"
    )
    
    on_track_count = models.IntegerField(
        default=0,
        help_text="Number of indicators on track"
    )
    
    at_risk_count = models.IntegerField(
        default=0,
        help_text="Number of indicators at risk"
    )
    
    # Metadata
    calculated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this score was last calculated"
    )
    
    is_dirty = models.BooleanField(
        default=False,
        help_text="Whether this score needs recalculation"
    )
    
    class Meta:
        db_table = 'esg_scoring_pillar_score'
        verbose_name = 'Pillar Score'
        verbose_name_plural = 'Pillar Scores'
        unique_together = [['organization', 'pillar', 'reporting_period']]
        indexes = [
            models.Index(fields=['organization', 'pillar', 'reporting_period']),
            models.Index(fields=['pillar', 'reporting_period']),
        ]
    
    def __str__(self):
        return f"{self.organization.name} - {self.get_pillar_display()} ({self.reporting_period.name}): {self.score:.1f}"
    
    def get_health_status(self):
        """Get health status based on score."""
        if self.score >= 76:
            return "Excellent"
        elif self.score >= 51:
            return "Good"
        elif self.score >= 26:
            return "Fair"
        else:
            return "Poor"
    
    def get_risk_percentage(self):
        """Calculate percentage of indicators at risk."""
        if self.indicator_count == 0:
            return 0
        return (self.at_risk_count / self.indicator_count) * 100
