"""Organization hierarchy services - Business logic for managing org structure."""
from typing import Dict, Any
from django.db import transaction
from django.core.exceptions import ValidationError

from common.logging import get_service_logger
from organizations.models import Organization, OrganizationSettings
from organizations.selectors.organization_hierarchy import (
    get_organization_descendants,
    is_descendant_of,
)

logger = get_service_logger("organizations.services")


@transaction.atomic
def create_subsidiary(
    parent_organization: Organization,
    name: str,
    sector: str,
    country: str,
    organization_type: str = "subsidiary",
    company_size: str = None,
    registered_name: str = None,
    primary_reporting_focus: str = None,
) -> Organization:
    """
    Create a subsidiary/child organization under a parent.
    
    Automatically:
    - Sets parent relationship
    - Inherits settings from parent
    - Creates default organization settings
    
    Args:
        parent_organization: Parent org
        name: Organization name
        sector: Sector code
        country: ISO 3166-1 alpha-2 country code
        organization_type: 'subsidiary' | 'facility' | 'department'
        company_size: Optional size category
        registered_name: Optional official name
        primary_reporting_focus: Inherited from parent if not specified
    
    Returns:
        Created Organization instance
    
    Raises:
        ValidationError: If parent is not valid or hierarchy would be circular
    
    Example:
        subsidiary = create_subsidiary(
            parent_organization=group_org,
            name="WACOT Rice Limited",
            sector="manufacturing",
            country="NG",
            organization_type="subsidiary"
        )
    """
    # Validate parent organization
    if not parent_organization or not parent_organization.is_active:
        raise ValidationError("Parent organization must be active and valid")
    
    # Use parent's reporting focus if not specified
    if not primary_reporting_focus:
        primary_reporting_focus = parent_organization.primary_reporting_focus
    
    # Create subsidiary
    child_org = Organization.objects.create(
        parent=parent_organization,
        name=name,
        sector=sector,
        country=country,
        organization_type=organization_type,
        company_size=company_size or parent_organization.company_size,
        registered_name=registered_name or name,
        primary_reporting_focus=primary_reporting_focus,
        is_active=True,
    )
    
    logger.info(
        f"Created {organization_type} '{name}' under parent '{parent_organization.name}'",
        extra={"org_id": child_org.id, "parent_id": parent_organization.id}
    )
    
    # Inherit settings from parent
    try:
        inherit_organizational_settings(parent_organization, child_org)
    except Exception as e:
        logger.warning(
            f"Failed to inherit settings from parent: {e}",
            extra={"org_id": child_org.id}
        )
        # Not critical - continue without inheriting settings
    
    return child_org


def inherit_organizational_settings(
    parent_organization: Organization,
    child_organization: Organization,
) -> OrganizationSettings:
    """
    Copy settings from parent org to child org.
    
    Used when creating subsidiaries to maintain consistent configuration.
    """
    # Get or create parent settings
    parent_settings, _ = OrganizationSettings.objects.get_or_create(
        organization=parent_organization
    )
    
    # Create child settings (copy from parent)
    child_settings, created = OrganizationSettings.objects.get_or_create(
        organization=child_organization,
        defaults={
            "system_language": parent_settings.system_language,
            "timezone": parent_settings.timezone,
            "currency": parent_settings.currency,
            "date_format": parent_settings.date_format,
            "admin_theme": parent_settings.admin_theme,
            "notifications_enabled": parent_settings.notifications_enabled,
            "system_update_frequency": parent_settings.system_update_frequency,
            "export_formats": parent_settings.export_formats,
            "security_checks_frequency": parent_settings.security_checks_frequency,
            "require_2fa": parent_settings.require_2fa,
            "encrypt_stored_data": parent_settings.encrypt_stored_data,
            "encryption_method": parent_settings.encryption_method,
        }
    )
    
    if created:
        logger.info(
            f"Inherited settings from parent org to '{child_organization.name}'",
            extra={"org_id": child_organization.id, "parent_id": parent_organization.id}
        )
    
    return child_settings


@transaction.atomic
def convert_to_group(organization: Organization) -> Organization:
    """
    Convert regular organization to group (parent company type).
    
    This allows an organization that was standalone to become a parent.
    """
    organization.organization_type = Organization.OrganizationType.GROUP
    organization.save(update_fields=["organization_type"])
    
    logger.info(
        f"Converted '{organization.name}' to group type",
        extra={"org_id": organization.id}
    )
    
    return organization


@transaction.atomic
def move_subsidiary(
    child_organization: Organization,
    new_parent: Organization,
) -> Organization:
    """
    Move subsidiary from one parent to another.
    
    Validates that move is valid (prevents circular hierarchies).
    
    Args:
        child_organization: Organization to move
        new_parent: New parent organization
    
    Returns:
        Updated Organization
    
    Raises:
        ValidationError: If move would create circular hierarchy
    """
    # Validate: ensure new_parent is not a descendant of child
    if is_descendant_of(new_parent, child_organization):
        raise ValidationError(
            "Cannot move organization: would create circular hierarchy"
        )
    
    old_parent = child_organization.parent
    child_organization.parent = new_parent
    child_organization.save(update_fields=["parent"])
    
    logger.info(
        f"Moved '{child_organization.name}' from "
        f"'{old_parent.name if old_parent else 'root'}' to '{new_parent.name}'",
        extra={"org_id": child_organization.id, "new_parent_id": new_parent.id}
    )
    
    return child_organization


@transaction.atomic
def consolidate_organization_esg_scores(organization: Organization) -> Dict[str, Any]:
    """
    Calculate consolidated ESG score across entire hierarchy.
    
    Aggregates ESG metrics from all descendants.
    
    Returns:
        {
            "organization_id": "uuid",
            "consolidated_score": 75.5,
            "component_scores": {
                "environmental": 80,
                "social": 75,
                "governance": 71
            },
            "descendants_count": 5,
            "submission_date": "2026-04-12T..."
        }
    
    Note:
        This is a placeholder for the ESG scoring engine.
        Will be implemented in next phase.
    """
    descendants = get_organization_descendants(
        organization,
        include_self=True
    ).values_list('id', flat=True)
    
    # TODO: Implement actual ESG scoring logic
    # For now, this is the interface
    
    return {
        "organization_id": str(organization.id),
        "consolidated_score": 0.0,
        "component_scores": {
            "environmental": 0,
            "social": 0,
            "governance": 0
        },
        "descendants_count": descendants.count(),
        "note": "ESG scoring logic to be implemented"
    }


def validate_hierarchy_structure(organization: Organization) -> Dict[str, Any]:
    """
    Validate that org hierarchy is valid and consistent.
    
    Checks:
    - No circular references
    - No broken parent links
    - Consistent organization types
    
    Returns:
        {
            "valid": True/False,
            "errors": [...],
            "warnings": [...]
        }
    """
    errors = []
    warnings = []
    
    # Check for circular references
    try:
        ancestors = []
        current = organization
        visited = set()
        
        while current:
            if current.id in visited:
                errors.append(f"Circular reference detected in hierarchy")
                break
            visited.add(current.id)
            current = current.parent
            
    except Exception as e:
        errors.append(f"Error checking hierarchy: {str(e)}")
    
    # Check organization type consistency
    if organization.organization_type == Organization.OrganizationType.GROUP:
        if organization.parent:
            warnings.append("Group should not have a parent organization")
    
    # Check parent consistency
    if organization.parent and not organization.parent.is_active:
        errors.append("Parent organization is inactive")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "organization_id": str(organization.id)
    }
