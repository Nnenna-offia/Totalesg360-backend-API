from django.db import models

from submissions.models.reporting_period import ReportingPeriod


class OrganizationESGSettings(models.Model):
    organization = models.OneToOneField(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="esg_settings",
    )

    enable_environmental = models.BooleanField(default=True)
    enable_social = models.BooleanField(default=True)
    enable_governance = models.BooleanField(default=True)

    reporting_level = models.CharField(
        max_length=20,
        choices=[
            ("group", "Group"),
            ("subsidiary", "Subsidiary"),
            ("facility", "Facility"),
            ("department", "Department"),
        ],
        default="subsidiary",
    )

    reporting_frequency = models.CharField(
        max_length=20,
        choices=ReportingPeriod.PeriodType.choices,
        default=ReportingPeriod.PeriodType.MONTHLY,
    )

    fiscal_year_start_month = models.IntegerField(default=1)
    sector_defaults = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "organizations_esg_settings"
        verbose_name = "Organization ESG Settings"
        verbose_name_plural = "Organization ESG Settings"

    def __str__(self):
        return f"{self.organization.name} ESG Settings"