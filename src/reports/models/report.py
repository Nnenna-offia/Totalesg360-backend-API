"""Report model - stores generated reports and metadata."""
from django.db import models
from django.conf import settings

from common.models import BaseModel
from organizations.models import Organization, RegulatoryFramework


class Report(BaseModel):
    """
    Stores ESG/Compliance/Framework reports with metadata and download links.
    
    Supports multiple report types aggregated from existing layers:
    - ESG Summary (from Layer 6 ESG Scoring)
    - Framework Reports (from Layer 5 Compliance Intelligence)
    - Group ESG Reports (from Layer 7 Group Consolidation)
    - Compliance Gap Reports (from Layer 5)
    - Partner Reports (stakeholder-specific views)
    """
    
    class ReportType(models.TextChoices):
        ESG_SUMMARY = "esg_summary", "ESG Summary"
        FRAMEWORK = "framework", "Framework"
        GROUP = "group", "Group ESG"
        GAP = "gap", "Compliance Gap"
        PARTNER = "partner", "Partner"

    class PartnerType(models.TextChoices):
        DEG = "deg", "Deutsche Entwicklungsgesellschaft"
        USAID = "usaid", "USAID"
        GCF = "gcf", "Green Climate Fund"
        FRC = "frc", "Facility for Recovery and Climate"
        NONE = "none", "Internal Only"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        GENERATING = "generating", "Generating"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="reports",
        db_index=True,
        help_text="Organization for which report was generated"
    )
    
    report_type = models.CharField(
        max_length=50,
        choices=ReportType.choices,
        db_index=True,
        help_text="Type of report"
    )
    
    framework = models.ForeignKey(
        RegulatoryFramework,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reports",
        help_text="Framework (for framework and partner reports)"
    )
    
    partner_type = models.CharField(
        max_length=20,
        choices=PartnerType.choices,
        default=PartnerType.NONE,
        help_text="Partner type (for partner reports)"
    )
    
    reporting_period_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="Reporting period ID for this report"
    )
    
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reports_generated",
        help_text="User who requested report generation"
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        help_text="Generation status"
    )
    
    file_url = models.URLField(
        null=True,
        blank=True,
        help_text="URL to download generated report (PDF/CSV/JSON)"
    )
    
    file_format = models.CharField(
        max_length=10,
        choices=[("pdf", "PDF"), ("csv", "CSV"), ("json", "JSON"), ("html", "HTML")],
        default="json",
        help_text="Export format"
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Report metadata (filters, parameters, etc.)"
    )
    
    summary = models.JSONField(
        default=dict,
        blank=True,
        help_text="Summary statistics for quick access"
    )
    
    generated_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When report was generated"
    )
    
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When report data expires (cache invalidation)"
    )

    class Meta:
        db_table = "reports_report"
        verbose_name = "Report"
        verbose_name_plural = "Reports"
        ordering = ["-generated_at"]
        indexes = [
            models.Index(fields=["organization", "report_type"]),
            models.Index(fields=["organization", "generated_at"]),
            models.Index(fields=["status", "generated_at"]),
        ]

    def __str__(self):
        return f"{self.get_report_type_display()} - {self.organization.name} ({self.generated_at.strftime('%Y-%m-%d')})"
