"""Selectors for user data."""
from typing import List, Dict, Any
from accounts.models import User


def get_user_memberships_with_roles(user: User) -> List[Dict[str, Any]]:
    """Get user's organization memberships with roles and capabilities.
    
    Args:
        user: User instance
        
    Returns:
        List of dicts containing organization, role, and capabilities info
    """
    memberships = user.memberships.filter(is_active=True).select_related(
        'organization',
        'role',
        'facility'
    ).prefetch_related(
        'role__role_capabilities__capability'
    )
    
    result = []
    for membership in memberships:
        # Get capabilities for this role through role_capabilities junction
        capabilities = [
            {
                "code": rc.capability.code,
                "name": rc.capability.name,
                "description": rc.capability.description,
            }
            for rc in membership.role.role_capabilities.select_related('capability')
        ]
        
        result.append({
            "organization": {
                "id": str(membership.organization.id),
                "name": membership.organization.name,
                "sector": membership.organization.sector,
                "country": str(membership.organization.country.code) if membership.organization.country else None,
            },
            "role": {
                "code": membership.role.code,
                "name": membership.role.name,
            },
            "capabilities": capabilities,
            "facility": {
                "id": str(membership.facility.id),
                "name": membership.facility.name,
            } if membership.facility else None,
            "is_active": membership.is_active,
            "joined_at": membership.joined_at.isoformat(),
        })
    
    return result
