from typing import Optional, Tuple
import re
from django.conf import settings

from organizations.models import Organization, Membership

UUID_RE = re.compile(r'^[0-9a-fA-F\-]{36}$')


def get_organization_by_identifier(identifier: str) -> Optional[Organization]:
    """Resolve an Organization by UUID, slug (if present) or case-insensitive name."""
    if not identifier:
        return None
    val = identifier.strip()
    try:
        if UUID_RE.match(val):
            return Organization.objects.filter(id=val, is_active=True).first()
        if hasattr(Organization, "slug"):
            return Organization.objects.filter(slug=val, is_active=True).first()
        return Organization.objects.filter(name__iexact=val, is_active=True).first()
    except Exception:
        return None


def get_user_membership_for_org(user, org: Organization) -> Optional[Membership]:
    if not user or not getattr(user, "is_authenticated", False) or not org:
        return None
    return (
        user.memberships.filter(organization=org, is_active=True)
        .select_related("role", "organization")
        .first()
    )


def get_org_and_membership(*, request=None, user=None, identifier: Optional[str] = None) -> Tuple[Optional[Organization], Optional[Membership]]:
    """Convenience helper to resolve organization and membership.

    Precedence:
      1. `request.organization` if present
      2. `identifier` (UUID/slug/name)
      3. Authenticated user's primary active membership
    """
    org = None
    if request is not None:
        org = getattr(request, "organization", None)
    if not org and identifier:
        org = get_organization_by_identifier(identifier)
    if not org and user is None and request is not None:
        user = getattr(request, "user", None)
    if not org and user and getattr(user, "is_authenticated", False):
        membership = user.memberships.filter(is_active=True).select_related("organization", "role").first()
        if membership:
            return membership.organization, membership
        return None, None
    membership = get_user_membership_for_org(user or getattr(request, "user", None), org) if org else None
    return org, membership
