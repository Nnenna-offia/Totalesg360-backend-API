"""Organization settings model for system configuration."""
from django.db import models
from django.core.validators import MinValueValidator
from common.models import BaseModel
from .organization import Organization


class OrganizationSettings(BaseModel):
    """
    Stores system configuration and preferences for an organization.
    OneToOne relationship with Organization.
    """
    
    class SystemLanguage(models.TextChoices):
        ENGLISH = "en", "English"
        FRENCH = "fr", "French"
        SPANISH = "es", "Spanish"
    
    class Timezone(models.TextChoices):
        UTC = "UTC", "UTC"
        WAT = "Africa/Lagos", "West Africa Time (WAT)"
        EAT = "Africa/Nairobi", "East Africa Time (EAT)"
        EST = "America/New_York", "Eastern Standard Time (EST)"
        PST = "America/Los_Angeles", "Pacific Standard Time (PST)"
    
    class Currency(models.TextChoices):
        USD = "USD", "US Dollar"
        EUR = "EUR", "Euro"
        GBP = "GBP", "British Pound"
        NGN = "NGN", "Nigerian Naira"
        ZAR = "ZAR", "South African Rand"
    
    class DateFormat(models.TextChoices):
        DMY = "DD/MM/YYYY", "Day/Month/Year"
        MDY = "MM/DD/YYYY", "Month/Day/Year"
        YMD = "YYYY-MM-DD", "Year-Month-Day"
    
    class AdminTheme(models.TextChoices):
        LIGHT = "light", "Light"
        DARK = "dark", "Dark"
        AUTO = "auto", "Auto (System)"
    
    class UpdateFrequency(models.TextChoices):
        REALTIME = "realtime", "Real-time"
        HOURLY = "hourly", "Hourly"
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"
    
    class EncryptionMethod(models.TextChoices):
        AES256 = "AES-256", "AES-256"
        AES128 = "AES-128", "AES-128"
        RSA = "RSA-2048", "RSA-2048"
    
    # OneToOne relationship with Organization
    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE,
        related_name="system_settings",
        help_text="Organization these settings belong to"
    )
    
    # General Settings
    system_language = models.CharField(
        max_length=5,
        choices=SystemLanguage.choices,
        default=SystemLanguage.ENGLISH,
        help_text="Primary system language"
    )
    
    timezone = models.CharField(
        max_length=50,
        choices=Timezone.choices,
        default=Timezone.UTC,
        help_text="Organization timezone"
    )
    
    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.USD,
        help_text="Default currency for financial data"
    )
    
    date_format = models.CharField(
        max_length=20,
        choices=DateFormat.choices,
        default=DateFormat.DMY,
        help_text="Date display format"
    )
    
    admin_theme = models.CharField(
        max_length=10,
        choices=AdminTheme.choices,
        default=AdminTheme.LIGHT,
        help_text="Admin interface theme"
    )
    
    notifications_enabled = models.BooleanField(
        default=True,
        help_text="Enable system notifications"
    )
    
    system_update_frequency = models.CharField(
        max_length=20,
        choices=UpdateFrequency.choices,
        default=UpdateFrequency.DAILY,
        help_text="How often to check for system updates"
    )
    
    security_checks_frequency = models.CharField(
        max_length=20,
        choices=UpdateFrequency.choices,
        default=UpdateFrequency.DAILY,
        help_text="How often to run security checks"
    )
    
    export_formats = models.JSONField(
        default=list,
        blank=True,
        help_text="Allowed export formats (e.g., ['pdf', 'xlsx', 'csv'])"
    )
    
    # Security Settings
    require_2fa = models.BooleanField(
        default=False,
        help_text="Require two-factor authentication for all users"
    )
    
    encrypt_stored_data = models.BooleanField(
        default=False,
        help_text="Encrypt sensitive data at rest"
    )
    
    encryption_method = models.CharField(
        max_length=20,
        choices=EncryptionMethod.choices,
        default=EncryptionMethod.AES256,
        help_text="Encryption algorithm for stored data"
    )
    # profile-related fields were moved into OrganizationProfile

    # Reporting frequencies and compliance flags
    local_reporting_frequency = models.CharField(
        max_length=20,
        choices=UpdateFrequency.choices,
        default=UpdateFrequency.DAILY,
        help_text="Local reporting frequency"
    )

    global_reporting_frequency = models.CharField(
        max_length=20,
        choices=UpdateFrequency.choices,
        default=UpdateFrequency.WEEKLY,
        help_text="Global reporting frequency"
    )

    auto_compliance_enabled = models.BooleanField(
        default=False,
        help_text="Whether automatic compliance checks are enabled"
    )
    
    class Meta:
        db_table = "organizations_settings"
        verbose_name = "Organization Settings"
        verbose_name_plural = "Organization Settings"
    
    def __str__(self):
        return f"Settings for {self.organization.name}"
