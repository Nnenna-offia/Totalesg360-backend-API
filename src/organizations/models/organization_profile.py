from django.db import models
from common.models import BaseModel
from .organization import Organization


class OrganizationProfile(BaseModel):
    """Holds company-specific profile information separated from settings."""

    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE,
        related_name="profile",
        help_text="Organization this profile belongs to",
    )

    registered_business_name = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Official registered business name",
    )

    cac_registration_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Company registration number (CAC)",
    )

    company_size = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ("small", "Small (1-50 employees)"),
            ("medium", "Medium (51-250 employees)"),
            ("large", "Large (251-1000 employees)"),
            ("enterprise", "Enterprise (1000+ employees)"),
        ],
        help_text="Organization size category",
    )

    logo = models.ImageField(
        upload_to="organization_logos/",
        blank=True,
        null=True,
        help_text="Organization logo",
    )

    operational_locations = models.JSONField(
        default=list,
        blank=True,
        help_text="List of operational locations",
    )

    fiscal_year_start_month = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[],
        help_text="Fiscal year start month (1-12)",
    )

    fiscal_year_end_month = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[],
        help_text="Fiscal year end month (1-12)",
    )

    cac_document = models.FileField(
        upload_to="organization_documents/",
        blank=True,
        null=True,
        help_text="Uploaded CAC registration document",
    )

    class Meta:
        db_table = "organizations_profile"
        verbose_name = "Organization Profile"
        verbose_name_plural = "Organization Profiles"

    def __str__(self):
        return f"Profile for {self.organization.name}"
