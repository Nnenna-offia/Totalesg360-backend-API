"""Compliance Recommendation model - AI-like recommendations to close compliance gaps."""
from django.db import models
from common.models import BaseModel
from organizations.models import Organization, RegulatoryFramework
from .framework_requirement import FrameworkRequirement


class ComplianceRecommendation(BaseModel):
    """
    Recommendations to close compliance gaps.
    
    Generated based on:
    1. Uncovered framework requirements
    2. Gap priority ranking
    3. Similar organization implementations
    4. Industry best practices
    
    Example recommendations:
    - "Add Scope 1 GHG Emissions Indicator (GRI 305-1)"
    - "Implement employee training tracking for skill development"
    - "Connect board oversight metrics to governance framework"
    """
    
    class RecommendationType(models.TextChoices):
        CREATE_INDICATOR = "create_indicator", "Create New Indicator"
        ENHANCE_DATA = "enhance_data", "Enhance Data Collection"
        INTEGRATE_SYSTEM = "integrate_system", "Integrate System/Data"
        IMPLEMENT_PROCESS = "implement_process", "Implement Process"
        TRAINING_REQUIRED = "training", "Training Required"
        GOVERNANCE_UPDATE = "governance", "Update Governance"
        OTHER = "other", "Other"
    
    class Priority(models.TextChoices):
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"
    
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        DEFERRED = "deferred", "Deferred"
    
    # Relationships
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="compliance_recommendations",
        db_index=True,
        help_text="Organization receiving recommendation"
    )
    
    framework = models.ForeignKey(
        RegulatoryFramework,
        on_delete=models.CASCADE,
        related_name="recommendations",
        db_index=True,
        help_text="Framework context"
    )
    
    requirement = models.ForeignKey(
        FrameworkRequirement,
        on_delete=models.CASCADE,
        related_name="recommendations",
        help_text="Requirement being addressed"
    )
    
    # Recommendation Details
    recommendation_type = models.CharField(
        max_length=50,
        choices=RecommendationType.choices,
        default=RecommendationType.CREATE_INDICATOR,
        help_text="Type of recommendation"
    )
    
    title = models.CharField(
        max_length=255,
        help_text="Short title of recommendation"
    )
    
    description = models.TextField(
        help_text="Detailed recommendation description"
    )
    
    actionable_steps = models.JSONField(
        default=list,
        help_text="Array of specific steps to implement"
    )
    
    # Impact & Priority
    impact_score = models.FloatField(
        default=0.0,
        validators=[],
        help_text="Expected impact on readiness score (0-10)"
    )
    
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        db_index=True,
        help_text="Priority of this recommendation"
    )
    
    # Implementation Guidance
    estimated_effort_days = models.IntegerField(
        default=0,
        help_text="Estimated implementation effort in days"
    )
    
    required_resources = models.TextField(
        blank=True,
        help_text="Resources/people needed to implement"
    )
    
    dependencies = models.JSONField(
        default=list,
        help_text="Requirements this depends on"
    )
    
    # Tracking
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        help_text="Current status of recommendation"
    )
    
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When implementation started"
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When recommendation was completed"
    )
    
    internal_notes = models.TextField(
        blank=True,
        help_text="Internal notes for compliance team"
    )
    
    generated_at = models.DateTimeField(
        auto_now=True,
        help_text="When recommendation was generated"
    )
    
    class Meta:
        db_table = "compliance_recommendation"
        verbose_name = "Compliance Recommendation"
        verbose_name_plural = "Compliance Recommendations"
        unique_together = [("organization", "framework", "requirement", "recommendation_type")]
        ordering = ["-priority", "-impact_score", "requirement__priority"]
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["organization", "priority"]),
            models.Index(fields=["framework", "priority"]),
            models.Index(fields=["status", "priority", "-impact_score"]),
        ]
    
    def __str__(self):
        return f"{self.organization.name} - {self.requirement.code}: {self.title}"
    
    def __repr__(self):
        return f"<ComplianceRecommendation {self.framework.code}/{self.requirement.code} {self.get_priority_display()}>"
    
    def is_high_impact(self) -> bool:
        """Returns True if impact score >= 7."""
        return self.impact_score >= 7
    
    def is_in_progress(self) -> bool:
        """Returns True if currently being implemented."""
        return self.status == self.Status.IN_PROGRESS
    
    def mark_in_progress(self):
        """Mark recommendation as in progress."""
        from django.utils import timezone
        self.status = self.Status.IN_PROGRESS
        self.started_at = timezone.now()
        self.save(update_fields=["status", "started_at"])
    
    def mark_completed(self):
        """Mark recommendation as completed."""
        from django.utils import timezone
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at"])
    
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
