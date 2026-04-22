"""Organization creation service."""
from django.db import transaction

from organizations.models import Organization
from organizations.services.hierarchy_validation import validate_hierarchy


@transaction.atomic
def create_organization(
    *,
    name: str,
    sector: str,
    country: str,
    primary_reporting_focus: str,
    entity_type: str = None,
    parent: Organization = None,
    registered_name: str = "",
    company_size: str = "",
    is_active: bool = True,
):
    """Create an organization with hierarchy validation."""
    resolved_entity_type = entity_type or (
        Organization.EntityType.SUBSIDIARY if parent else Organization.EntityType.GROUP
    )
    validate_hierarchy(parent, resolved_entity_type)

    return Organization.objects.create(
        name=name,
        sector=sector,
        country=country,
        primary_reporting_focus=primary_reporting_focus,
        entity_type=resolved_entity_type,
        parent=parent,
        registered_name=registered_name or name,
        company_size=company_size or "",
        is_active=is_active,
    )