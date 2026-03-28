from typing import Optional
import re

from rest_framework import permissions
from django.conf import settings

from organizations.models import Organization

UUID_RE = re.compile(r'^[0-9a-fA-F\-]{36}$')


def _resolve_org_from_header(request) -> Optional[Organization]:
    header = getattr(settings, "ORG_HEADER_NAME", "X-ORG-ID")
    # DRF provides request.headers; WSGI uses HTTP_ prefix
    val = request.headers.get(header) or request.META.get(f"HTTP_{header.replace('-', '_').upper()}")
    if not val:
        return None
    val = val.strip()
    try:
        if UUID_RE.match(val):
            return Organization.objects.filter(id=val, is_active=True).first()
        if hasattr(Organization, "slug"):
            return Organization.objects.filter(slug=val, is_active=True).first()
        return Organization.objects.filter(name__iexact=val, is_active=True).first()
    except Exception:
        return None


def _get_org(request) -> Optional[Organization]:
    org = getattr(request, "organization", None)
    if org:
        return org
    return _resolve_org_from_header(request)


class IsOrgMember(permissions.BasePermission):
    """Allow only users who are active members of the resolved organization."""

    message = "User is not a member of the organization."

    def has_permission(self, request, view):
        org = _get_org(request)
        if not org:
            return False
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False
        membership = (
            user.memberships.filter(organization=org, is_active=True)
            .select_related("role")
            .first()
        )
        return membership is not None


class HasCapability(permissions.BasePermission):

    message = "User lacks required capability for this organization."

    def has_permission(self, request, view):
        required = getattr(view, "required_capability", None)
        if not required:
            return True

        org = _get_org(request)
        if not org:
            return False

        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        return user.memberships.filter(
            organization=org,
            is_active=True,
            role__role_capabilities__capability__code=required,
            role__role_capabilities__is_active=True
        ).exists()


class HasGlobalCapability(permissions.BasePermission):
    """Check that the authenticated user has the given capability on any of their roles
    or is staff. View should set `required_capability` attribute.
    """

    message = "User lacks required global capability."

    def has_permission(self, request, view):
        required = getattr(view, "required_capability", None)
        if not required:
            return True
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False
        # staff bypass
        if getattr(user, "is_staff", False):
            return True
        # any membership role with the capability
        return user.memberships.filter(role__role_capabilities__capability__code=required).exists()
