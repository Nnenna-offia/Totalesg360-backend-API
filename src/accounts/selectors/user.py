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

    # Aggregate by organization to avoid duplicated organization blocks
    grouped = {}
    for membership in memberships:
        org_id = str(membership.organization.id)
        # Build capability list for this role
        role_caps = [
            {
                "code": rc.capability.code,
                "name": rc.capability.name,
                "description": rc.capability.description,
            }
            for rc in membership.role.role_capabilities.select_related('capability')
        ]

        if org_id not in grouped:
            grouped[org_id] = {
                "organization": {
                    "id": org_id,
                    "name": membership.organization.name,
                    "sector": membership.organization.sector,
                    "country": str(membership.organization.country.code) if membership.organization.country else None,
                },
                "roles": [],
                "capabilities_set": {},
                "facilities": [],
                "is_active": False,
                "joined_at": None,
            }

        g = grouped[org_id]

        # append role
        g["roles"].append({"code": membership.role.code, "name": membership.role.name})

        # add capabilities into a dict keyed by code to dedupe while preserving a sample name/desc
        for c in role_caps:
            if c["code"] not in g["capabilities_set"]:
                g["capabilities_set"][c["code"]] = c

        # facilities (may be None)
        if membership.facility:
            fac = {"id": str(membership.facility.id), "name": membership.facility.name}
            if fac not in g["facilities"]:
                g["facilities"].append(fac)

        # compute is_active if any membership is active
        g["is_active"] = g["is_active"] or bool(membership.is_active)

        # joined_at: keep earliest join date if present
        try:
            j = membership.joined_at
            if j:
                iso = j.isoformat()
                if not g["joined_at"] or iso < g["joined_at"]:
                    g["joined_at"] = iso
        except Exception:
            pass

    # Build final list converting capability dict back to list and removing helper keys
    result = []
    for org_id, g in grouped.items():
        caps = list(g["capabilities_set"].values())
        result.append({
            "organization": g["organization"],
            "role": g["roles"][0] if g["roles"] else None,
            "roles": g["roles"],
            "capabilities": caps,
            "facility": g["facilities"][0] if g["facilities"] else None,
            "facilities": g["facilities"] if g["facilities"] else None,
            "is_active": g["is_active"],
            "joined_at": g["joined_at"],
        })

    return result
