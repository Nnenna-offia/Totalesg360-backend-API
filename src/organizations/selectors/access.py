from django.conf import settings
from django.shortcuts import get_object_or_404
from organizations.models.organization import Organization


def get_organization_by_id(org_id):
    """Return Organization instance or None if not found."""
    if not org_id:
        return None
    try:
        return Organization.objects.get(id=org_id)
    except Organization.DoesNotExist:
        return None


def user_belongs_to_org(user, org_id):
    """Return True if `user` has an active membership on the org with id `org_id`."""
    if user is None or not getattr(user, 'is_authenticated', False):
        return False
    if not org_id:
        return False
    return user.memberships.filter(organization_id=org_id, is_active=True).exists()
