"""Services for organization settings management."""
from typing import Dict, Any
from django.db import transaction
from django.core.exceptions import ValidationError
from organizations.models import OrganizationSettings, Organization


@transaction.atomic
def update_general_settings(
    organization: Organization,
    system_language: str = None,
    timezone: str = None,
    currency: str = None,
    date_format: str = None,
    admin_theme: str = None,
    notifications_enabled: bool = None,
    system_update_frequency: str = None,
    export_formats: list = None,
    local_reporting_frequency: str = None,
    global_reporting_frequency: str = None,
) -> OrganizationSettings:
    """
    Update general settings for an organization.
    
    Args:
        organization: Organization instance
        system_language: Primary system language
        timezone: Organization timezone
        currency: Default currency
        date_format: Date display format
        admin_theme: Admin interface theme
        notifications_enabled: Enable system notifications
        system_update_frequency: Update check frequency
        export_formats: Allowed export formats
        
    Returns:
        Updated OrganizationSettings instance
        
    Raises:
        ValidationError: If validation fails
    """
    # Get or create settings
    settings, _ = OrganizationSettings.objects.get_or_create(
        organization=organization
    )
    
    # Update fields if provided
    if system_language is not None:
        if system_language not in dict(OrganizationSettings.SystemLanguage.choices):
            raise ValidationError(f"Invalid system_language: {system_language}")
        settings.system_language = system_language
    
    if timezone is not None:
        if timezone not in dict(OrganizationSettings.Timezone.choices):
            raise ValidationError(f"Invalid timezone: {timezone}")
        settings.timezone = timezone
    
    if currency is not None:
        if currency not in dict(OrganizationSettings.Currency.choices):
            raise ValidationError(f"Invalid currency: {currency}")
        settings.currency = currency
    
    if date_format is not None:
        if date_format not in dict(OrganizationSettings.DateFormat.choices):
            raise ValidationError(f"Invalid date_format: {date_format}")
        settings.date_format = date_format
    
    if admin_theme is not None:
        if admin_theme not in dict(OrganizationSettings.AdminTheme.choices):
            raise ValidationError(f"Invalid admin_theme: {admin_theme}")
        settings.admin_theme = admin_theme
    
    if notifications_enabled is not None:
        settings.notifications_enabled = notifications_enabled
    
    if system_update_frequency is not None:
        if system_update_frequency not in dict(OrganizationSettings.UpdateFrequency.choices):
            raise ValidationError(f"Invalid system_update_frequency: {system_update_frequency}")
        settings.system_update_frequency = system_update_frequency
    
    # reporting frequencies
    if 'local_reporting_frequency' in locals() or False:
        pass

    
    if export_formats is not None:
        if not isinstance(export_formats, list):
            raise ValidationError("export_formats must be a list")
        settings.export_formats = export_formats

    # support optional local/global reporting frequency when provided in kwargs
    local = locals().get('local_reporting_frequency', None)
    if local is not None:
        if local not in dict(OrganizationSettings.UpdateFrequency.choices):
            raise ValidationError(f"Invalid local_reporting_frequency: {local}")
        settings.local_reporting_frequency = local

    global_rf = locals().get('global_reporting_frequency', None)
    if global_rf is not None:
        if global_rf not in dict(OrganizationSettings.UpdateFrequency.choices):
            raise ValidationError(f"Invalid global_reporting_frequency: {global_rf}")
        settings.global_reporting_frequency = global_rf
    
    settings.save()
    return settings


@transaction.atomic
def update_security_settings(
    organization: Organization,
    security_checks_frequency: str = None,
    require_2fa: bool = None,
    encrypt_stored_data: bool = None,
    encryption_method: str = None,
    auto_compliance_enabled: bool = None
) -> OrganizationSettings:
    """
    Update security settings for an organization.
    
    Args:
        organization: Organization instance
        security_checks_frequency: Security check frequency
        require_2fa: Require two-factor authentication
        encrypt_stored_data: Encrypt sensitive data at rest
        encryption_method: Encryption algorithm
        
    Returns:
        Updated OrganizationSettings instance
        
    Raises:
        ValidationError: If validation fails
    """
    # Get or create settings
    settings, _ = OrganizationSettings.objects.get_or_create(
        organization=organization
    )
    
    # Update fields if provided
    if security_checks_frequency is not None:
        if security_checks_frequency not in dict(OrganizationSettings.UpdateFrequency.choices):
            raise ValidationError(f"Invalid security_checks_frequency: {security_checks_frequency}")
        settings.security_checks_frequency = security_checks_frequency
    
    if require_2fa is not None:
        settings.require_2fa = require_2fa
    
    if encrypt_stored_data is not None:
        settings.encrypt_stored_data = encrypt_stored_data
    
    if encryption_method is not None:
        if encryption_method not in dict(OrganizationSettings.EncryptionMethod.choices):
            raise ValidationError(f"Invalid encryption_method: {encryption_method}")
        settings.encryption_method = encryption_method
    
    # auto compliance flag
    auto_comp = locals().get('auto_compliance_enabled', None)
    if auto_comp is not None:
        settings.auto_compliance_enabled = bool(auto_comp)
    
    settings.save()
    return settings


@transaction.atomic
def update_preferences_settings(
    organization: Organization,
    system_language: str = None,
    timezone: str = None,
    date_format: str = None,
    admin_theme: str = None,
    notifications_enabled: bool = None,
    system_update_frequency: str = None,
    export_formats: list = None
) -> OrganizationSettings:
    """
    Update user preference settings for an organization.
    
    Args:
        organization: Organization instance
        system_language: Primary system language
        timezone: Organization timezone
        date_format: Date display format
        admin_theme: Admin interface theme
        notifications_enabled: Enable system notifications
        system_update_frequency: Update check frequency
        export_formats: Allowed export formats
        
    Returns:
        Updated OrganizationSettings instance
        
    Raises:
        ValidationError: If validation fails
    """
    # Get or create settings
    settings, _ = OrganizationSettings.objects.get_or_create(
        organization=organization
    )
    
    # Update preference fields if provided
    if system_language is not None:
        if system_language not in dict(OrganizationSettings.SystemLanguage.choices):
            raise ValidationError(f"Invalid system_language: {system_language}")
        settings.system_language = system_language
    
    if timezone is not None:
        if timezone not in dict(OrganizationSettings.Timezone.choices):
            raise ValidationError(f"Invalid timezone: {timezone}")
        settings.timezone = timezone
    
    if date_format is not None:
        if date_format not in dict(OrganizationSettings.DateFormat.choices):
            raise ValidationError(f"Invalid date_format: {date_format}")
        settings.date_format = date_format
    
    if admin_theme is not None:
        if admin_theme not in dict(OrganizationSettings.AdminTheme.choices):
            raise ValidationError(f"Invalid admin_theme: {admin_theme}")
        settings.admin_theme = admin_theme
    
    if notifications_enabled is not None:
        settings.notifications_enabled = notifications_enabled
    
    if system_update_frequency is not None:
        if system_update_frequency not in dict(OrganizationSettings.UpdateFrequency.choices):
            raise ValidationError(f"Invalid system_update_frequency: {system_update_frequency}")
        settings.system_update_frequency = system_update_frequency
    
    if export_formats is not None:
        if not isinstance(export_formats, list):
            raise ValidationError("export_formats must be a list")
        settings.export_formats = export_formats
    
    settings.save()
    return settings


@transaction.atomic
def update_compliance_settings(
    organization: Organization,
    local_reporting_frequency: str = None,
    global_reporting_frequency: str = None,
    currency: str = None
) -> OrganizationSettings:
    """
    Update compliance-related settings for an organization.
    
    Args:
        organization: Organization instance
        local_reporting_frequency: Local reporting frequency
        global_reporting_frequency: Global reporting frequency
        currency: Default currency for reports
        
    Returns:
        Updated OrganizationSettings instance
        
    Raises:
        ValidationError: If validation fails
    """
    # Get or create settings
    settings, _ = OrganizationSettings.objects.get_or_create(
        organization=organization
    )
    
    # Update compliance fields if provided
    if local_reporting_frequency is not None:
        if local_reporting_frequency not in dict(OrganizationSettings.UpdateFrequency.choices):
            raise ValidationError(f"Invalid local_reporting_frequency: {local_reporting_frequency}")
        settings.local_reporting_frequency = local_reporting_frequency
    
    if global_reporting_frequency is not None:
        if global_reporting_frequency not in dict(OrganizationSettings.UpdateFrequency.choices):
            raise ValidationError(f"Invalid global_reporting_frequency: {global_reporting_frequency}")
        settings.global_reporting_frequency = global_reporting_frequency
    
    if currency is not None:
        if currency not in dict(OrganizationSettings.Currency.choices):
            raise ValidationError(f"Invalid currency: {currency}")
        settings.currency = currency
    
    settings.save()
    return settings
