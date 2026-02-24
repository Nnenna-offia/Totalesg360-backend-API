import re
from typing import Optional
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

from organizations.models import Organization

UUID_RE = re.compile(r'^[0-9a-fA-F\-]{36}$')


class OrganizationContextMiddleware(MiddlewareMixin):
    """Attach `request.organization`, `request.membership`, and `request.role`.

    Resolution precedence:
      1. `ORG_HEADER_NAME` header (default `X-ORG-ID`)
      2. Subdomain (if `ORG_SUBDOMAIN_ENABLED` True and Organization.subdomain/slug exists)
      3. Authenticated user's first active membership

    Notes:
      - Middleware is permissive: header/subdomain can select an org even if the
        authenticated user is not a member. Authorization should be enforced by
        permissions (e.g., `IsOrgMember`, `HasCapability`).
    """

    header_name = getattr(settings, "ORG_HEADER_NAME", "X-ORG-ID")
    subdomain_enabled = getattr(settings, "ORG_SUBDOMAIN_ENABLED", False)

    def process_request(self, request):
        request.organization = None
        request.membership = None
        request.role = None

        org = self._from_header(request) or self._from_subdomain(request) or self._from_user_primary(request)

        if org:
            request.organization = org
            user = getattr(request, "user", None)
            if user and getattr(user, "is_authenticated", False):
                membership = (
                    user.memberships.filter(organization=org, is_active=True)
                    .select_related("role", "organization")
                    .first()
                )
                if membership:
                    request.membership = membership
                    request.role = membership.role

    def _from_header(self, request) -> Optional[Organization]:
        val = request.headers.get(self.header_name) or request.META.get(f"HTTP_{self.header_name.replace('-', '_').upper()}")
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

    def _from_subdomain(self, request) -> Optional[Organization]:
        if not self.subdomain_enabled:
            return None
        host = request.get_host().split(":")[0]
        parts = host.split(".")
        if len(parts) < 3:
            return None
        sub = parts[0]
        try:
            if hasattr(Organization, "subdomain"):
                return Organization.objects.filter(subdomain=sub, is_active=True).first()
            if hasattr(Organization, "slug"):
                return Organization.objects.filter(slug=sub, is_active=True).first()
            if UUID_RE.match(sub):
                return Organization.objects.filter(id=sub, is_active=True).first()
        except Exception:
            return None
        return None

    def _from_user_primary(self, request) -> Optional[Organization]:
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return None
        membership = user.memberships.filter(is_active=True).select_related("organization", "role").first()
        return membership.organization if membership else None
