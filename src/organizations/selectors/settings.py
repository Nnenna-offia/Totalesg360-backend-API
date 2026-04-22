"""Selectors for organization settings."""
from typing import Optional
from django.db.models import Prefetch
from organizations.models import Organization, OrganizationSettings, Department, OrganizationESGSettings


def get_organization_settings(organization_id: str) -> Optional[dict]:
    """
    Retrieve organization settings with related data.
    
    Args:
        organization_id: UUID of the organization
        
    Returns:
        Dictionary with organization, settings, departments, and frameworks
    """
    try:
        organization = Organization.objects.prefetch_related(
            Prefetch(
                'departments',
                queryset=Department.objects.filter(is_active=True).order_by('name')
            ),
            'framework_assignments__framework'
        ).select_related('system_settings').get(id=organization_id)
        
        # Ensure settings and profile exist
        settings, _ = OrganizationSettings.objects.get_or_create(
            organization=organization
        )
        esg_settings, _ = OrganizationESGSettings.objects.get_or_create(
            organization=organization,
            defaults={"reporting_level": organization.entity_type},
        )
        # profile may be created on migration or on demand
        try:
            profile = organization.profile
        except Exception:
            from organizations.models import OrganizationProfile
            profile, _ = OrganizationProfile.objects.get_or_create(organization=organization)
        
        frameworks = list(organization.framework_assignments.all())
        
        return {
            'organization': organization,
            'company': profile,
            'general': settings,
            'settings': settings,
            'esg_settings': esg_settings,
            'departments': list(organization.departments.all()),
            'frameworks': frameworks
        }
    except Organization.DoesNotExist:
        return None


def get_organization_with_settings(organization_id: str) -> Optional[Organization]:
    """
    Retrieve organization with its settings.
    
    Args:
        organization_id: UUID of the organization
        
    Returns:
        Organization instance with settings or None
    """
    try:
        org = Organization.objects.select_related('system_settings').get(id=organization_id)
        # Ensure settings exist
        if not hasattr(org, 'system_settings'):
            OrganizationSettings.objects.create(organization=org)
            org.refresh_from_db()
        return org
    except Organization.DoesNotExist:
        return None
