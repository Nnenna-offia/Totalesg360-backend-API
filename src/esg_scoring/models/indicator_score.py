"""Indicator Score model - stores calculated scores for individual indicators."""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from common.models import BaseModel
from organizations.models import Organization
from indicators.models import Indicator
from submissions.models import ReportingPeriod


class IndicatorScore(BaseModel):
    """
    Stores calculated scores for individual indicators per organization per reporting period.
    
    Indicator Score is the foundation of the scoring hierarchy:
    Indicator Scores → Pillar Scores → Organization ESG Score → Group ESG Score
    """
    
    class ScoreStatus(models.TextChoices):
        POOR = "poor", "Poor (0-25%)"
        AT_RISK = "at_risk", "At Risk (26-50%)"
        ON_TRACK = "on_track", "On Track (51-75%)"
        ACHIEVED = "achieved", "Achieved (76-100%)"
    
    # Relationships
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="indicator_scores",
        db_index=True,
        help_text="Organization being scored"
    )
    
    indicator = models.ForeignKey(
        Indicator,
        on_delete=models.CASCADE,
        related_name="scores",
        db_index=True,
        help_text="Indicator being scored"
    )
    
    reporting_period = models.ForeignKey(
        ReportingPeriod,
        on_delete=models.CASCADE,
        related_name="indicator_scores",
        db_index=True,
        help_text="Reporting period for this score"
    )
    
    # Score Data
    score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Calculated indicator score (0-100)"
    )
    
    value = models.FloatField(
        null=True,
        blank=True,
        help_text="Actual reported value for the indicator"
    )
    
    target = models.FloatField(
        null=True,
        blank=True,
        help_text="Target value for the indicator"
    )
    
    baseline = models.FloatField(
        null=True,
        blank=True,
        help_text="Baseline value for comparison"
    )
    
    progress = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Progress toward target (0-100%)"
    )
    
    # Status & Metadata
    status = models.CharField(
        max_length=20,
        choices=ScoreStatus.choices,
        default=ScoreStatus.ON_TRACK,
        db_index=True,
        help_text="Status indicator (poor, at_risk, on_track, achieved)"
    )
    
    # Calculation Metadata
    calculation_method = models.CharField(
        max_length=50,
        blank=True,
        help_text="Method used to calculate score (e.g., 'linear', 'weighted', 'custom')"
    )
    
    note = models.TextField(
        blank=True,
        help_text="Notes about the calculation or score"
    )
    
    calculated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this score was last calculated"
    )
    
    is_manual = models.BooleanField(
        default=False,
        help_text="Whether score was manually entered vs auto-calculated"
    )
    
    class Meta:
        db_table = 'esg_scoring_indicator_score'
        verbose_name = 'Indicator Score'
        verbose_name_plural = 'Indicator Scores'
        unique_together = [['organization', 'indicator', 'reporting_period']]
        indexes = [
            models.Index(fields=['organization', 'reporting_period']),
            models.Index(fields=['indicator', 'reporting_period']),
            models.Index(fields=['status', 'reporting_period']),
        ]
    
    def __str__(self):
        return f"{self.organization.name} - {self.indicator.name} ({self.reporting_period.name}): {self.score:.1f}"
    
    def is_on_track(self):
        """Check if indicator score is on track or achieved."""
        return self.status in [self.ScoreStatus.ON_TRACK, self.ScoreStatus.ACHIEVED]
    
    def is_at_risk(self):
        """Check if indicator score is poor or at risk."""
        return self.status in [self.ScoreStatus.POOR, self.ScoreStatus.AT_RISK]
