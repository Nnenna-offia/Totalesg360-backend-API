"""Selectors for user data."""
from typing import List, Dict, Any, Optional
from accounts.models import User, EmailVerification


def user_exists_by_email(email: str) -> bool:
    """Check if a user exists with the given email.
    
    Args:
        email: User email address
        
    Returns:
        True if user exists, False otherwise
    """
    return User.objects.filter(email=email).exists()


def get_user_by_email(email: str) -> Optional[User]:
    """Get a user by email address.
    
    Args:
        email: User email address
        
    Returns:
        User instance if found, None otherwise
    """
    return User.objects.filter(email=email).first()


def get_latest_email_verification_for_user(user: User) -> Optional[EmailVerification]:
    """Get the most recent email verification record for a user.
    
    Args:
        user: User instance
        
    Returns:
        Latest EmailVerification instance if exists, None otherwise
    """
    return EmailVerification.objects.filter(user=user).order_by("-created_at").first()


def email_verification_exists_for_user(user: User) -> bool:
    """Check if an email verification record exists for a user.
    
    Args:
        user: User instance
        
    Returns:
        True if email verification exists, False otherwise
    """
    return EmailVerification.objects.filter(user=user).exists()


def password_reset_exists_for_user(user: User) -> bool:
    """Check if a password reset record exists for a user."""
    from accounts.models import PasswordReset
    return PasswordReset.objects.filter(user=user).exists()


def get_latest_password_reset_for_user(user: User) -> Optional["PasswordReset"]:
    """Get the most recent password reset record for a user."""
    from accounts.models import PasswordReset
    return PasswordReset.objects.filter(user=user).order_by("-created_at").first()


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
