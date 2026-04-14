"""ESG Score model - overall ESG scores combining all pillars."""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from common.models import BaseModel
from organizations.models import Organization
from submissions.models import ReportingPeriod


class ESGScore(BaseModel):
    """
    Stores overall ESG scores for organization.
    
    Score Hierarchy:
    Indicator Scores → Pillar Scores → Organization ESG Score → Group ESG Score
    """
    
    # Relationships
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="esg_scores",
        db_index=True,
        help_text="Organization being scored"
    )
    
    reporting_period = models.ForeignKey(
        ReportingPeriod,
        on_delete=models.CASCADE,
        related_name="esg_scores",
        db_index=True,
        help_text="Reporting period for this score"
    )
    
    # Pillar Scores
    environmental_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Environmental pillar score (0-100)"
    )
    
    social_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Social pillar score (0-100)"
    )
    
    governance_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Governance pillar score (0-100)"
    )
    
    # Overall Score
    overall_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Weighted average of E/S/G scores (0-100)"
    )
    
    # Weighting Configuration
    environmental_weight = models.FloatField(
        default=0.4,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Weight for environmental score (default 0.4)"
    )
    
    social_weight = models.FloatField(
        default=0.3,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Weight for social score (default 0.3)"
    )
    
    governance_weight = models.FloatField(
        default=0.3,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Weight for governance score (default 0.3)"
    )
    
    # Metadata
    calculated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this score was last calculated"
    )
    
    is_consolidated = models.BooleanField(
        default=False,
        db_index=True,
        help_text="True for group consolidation, False for individual organization"
    )
    
    is_dirty = models.BooleanField(
        default=False,
        help_text="Whether this score needs recalculation"
    )
    
    class Meta:
        db_table = 'esg_scoring_esg_score'
        verbose_name = 'ESG Score'
        verbose_name_plural = 'ESG Scores'
        unique_together = [['organization', 'reporting_period']]
        indexes = [
            models.Index(fields=['organization', 'reporting_period']),
            models.Index(fields=['is_consolidated', 'reporting_period']),
        ]
    
    def __str__(self):
        score_type = "Group" if self.is_consolidated else "Org"
        return f"{self.organization.name} - {score_type} ESG ({self.reporting_period.name}): {self.overall_score:.1f}"
    
    def get_score_distribution(self):
        """Get dictionary of E/S/G scores."""
        return {
            'environmental': round(self.environmental_score, 2),
            'social': round(self.social_score, 2),
            'governance': round(self.governance_score, 2),
            'overall': round(self.overall_score, 2),
        }
    
    def get_pillar_ranking(self):
        """Get pillars ranked by score (highest to lowest)."""
        pillars = [
            ('Environmental', self.environmental_score),
            ('Social', self.social_score),
            ('Governance', self.governance_score),
        ]
        return [name for name, score in sorted(pillars, key=lambda x: x[1], reverse=True)]
    
    def get_strengths(self):
        """Get pillars with score >= 70 (strengths)."""
        pillars = {
            'Environmental': self.environmental_score,
            'Social': self.social_score,
            'Governance': self.governance_score,
        }
        return {name: score for name, score in pillars.items() if score >= 70}
    
    def get_weaknesses(self):
        """Get pillars with score < 50 (weaknesses)."""
        pillars = {
            'Environmental': self.environmental_score,
            'Social': self.social_score,
            'Governance': self.governance_score,
        }
        return {name: score for name, score in pillars.items() if score < 50}
