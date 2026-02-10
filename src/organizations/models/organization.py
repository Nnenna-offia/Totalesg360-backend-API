# organizations/models/organization.py
from django.db import models
from common.models import BaseModel
from django_countries.fields import CountryField


class Organization(BaseModel):
    """
    Represents a company/entity using the ESG platform.
    Settings field stores sector-specific configuration (dropdowns, scopes, etc.).
    """
    
    class PrimaryReportingFocus(models.TextChoices):
        NIGERIA = "NIGERIA", "Nigeria Regulators Only"
        INTERNATIONAL = "INTERNATIONAL", "International Frameworks Only"
        HYBRID = "HYBRID", "Nigeria + International (Hybrid)"
    
    name = models.CharField(max_length=255, unique=True)
    sector = models.CharField(
        max_length=50,
        choices=[
            ("manufacturing", "Manufacturing"),
            ("oil_gas", "Oil & Gas"),
            ("finance", "Finance"),
        ],
    )
    country = CountryField(blank_label='(select country)', help_text="Organization's country")
    
    primary_reporting_focus = models.CharField(
        max_length=20,
        choices=PrimaryReportingFocus.choices,
        default=PrimaryReportingFocus.NIGERIA,
        help_text="Primary reporting focus: Nigeria only, International only, or Hybrid"
    )
    
    # Many-to-many relationship with frameworks
    regulatory_frameworks = models.ManyToManyField(
        "organizations.RegulatoryFramework",
        through="organizations.OrganizationFramework",
        related_name="organizations",
        help_text="Assigned regulatory frameworks"
    )
    
    # Config-driven: stores sector-specific settings, scopes, permits, etc.
    settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Sector-specific configuration (scopes, permits, frameworks)"
    )
    
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'organizations_organization'
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'
        indexes = [
            models.Index(fields=['sector', 'is_active']),
            models.Index(fields=['primary_reporting_focus']),
        ]

    def __str__(self):
        return self.name
