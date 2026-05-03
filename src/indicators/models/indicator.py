from django.db import models
from common.models import BaseModel


class Indicator(BaseModel):
    class Pillar(models.TextChoices):
        ENVIRONMENTAL = "ENV", "Environmental"
        SOCIAL = "SOC", "Social"
        GOVERNANCE = "GOV", "Governance"

    class DataType(models.TextChoices):
        NUMBER = "number", "Number"
        PERCENT = "percent", "Percent"
        BOOLEAN = "boolean", "Boolean"
        TEXT = "text", "Text"
        CURRENCY = "currency", "Currency"

    class CollectionMethod(models.TextChoices):
        ACTIVITY = "activity", "Activity Based"
        DIRECT = "direct", "Direct Submission"

    class IndicatorType(models.TextChoices):
        INPUT = "INPUT", "Input"
        DERIVED = "DERIVED", "Derived"

    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    pillar = models.CharField(max_length=8, choices=Pillar.choices, db_index=True)
    data_type = models.CharField(max_length=20, choices=DataType.choices, db_index=True)
    unit = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)
    version = models.CharField(max_length=16, blank=True, null=True)
    
    # Collection method: how indicator values are obtained
    collection_method = models.CharField(
        max_length=20,
        choices=CollectionMethod.choices,
        default=CollectionMethod.DIRECT,
        db_index=True,
        help_text="Activity-based indicators are calculated from activities; direct indicators are manually submitted"
    )

    indicator_type = models.CharField(
        max_length=20,
        choices=IndicatorType.choices,
        default=IndicatorType.INPUT,
        db_index=True,
        help_text="INPUT indicators store raw operational data; DERIVED indicators are calculated outputs.",
    )
    emission_factor = models.FloatField(null=True, blank=True)
    calculation_method = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = "indicators_indicator"
        verbose_name = "Indicator"
        verbose_name_plural = "Indicators"
        indexes = [
            models.Index(fields=["pillar"]),
            models.Index(fields=["data_type"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["indicator_type"]),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class OrganizationIndicator(BaseModel):
    """Tenant-level indicator configuration / overrides.

    `is_required` is nullable: None = inherit framework-derived requirement; True/False = override.
    """

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="organization_indicators",
    )
    indicator = models.ForeignKey(
        "indicators.Indicator",
        on_delete=models.PROTECT,
        related_name="organization_overrides",
    )
    is_required = models.BooleanField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    

    class Meta:
        db_table = "indicators_organizationindicator"
        verbose_name = "Organization Indicator"
        verbose_name_plural = "Organization Indicators"
        unique_together = (("organization", "indicator"),)
        indexes = [
            models.Index(fields=["organization", "is_active"]),
        ]

    def __str__(self):
        return f"{self.organization} - {self.indicator.code}"
