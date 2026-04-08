from django.conf import settings
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from organizations.selectors import get_organization_by_id, user_belongs_to_org


class OrgHeaderMissing(ValidationError):
    default_detail = 'X-ORG-ID header is required'


class OrgNotFound(NotFound):
    default_detail = 'Organization not found'


class UserNotInOrg(PermissionDenied):
    default_detail = 'You do not belong to this organization'


def validate_user_organization(request):
    """
    Validate `X-ORG-ID` header, ensure organization exists and request.user
    is a member. Returns Organization instance on success or raises DRF errors.
    """
    header_name = getattr(settings, 'ORG_HEADER_NAME', 'X-ORG-ID')
    org_id = request.headers.get(header_name) or request.META.get(f'HTTP_{header_name.replace("-","_").upper()}')

    if not org_id:
        raise OrgHeaderMissing()

    org = get_organization_by_id(org_id)
    if org is None:
        raise OrgNotFound()

    user = getattr(request, 'user', None)
    if not user_belongs_to_org(user, org_id):
        raise UserNotInOrg()

    return org
