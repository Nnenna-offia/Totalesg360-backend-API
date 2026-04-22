"""Organization hierarchy selectors - Read-only queries for org structure."""
from typing import List, Dict, Any
from django.db.models import QuerySet

from organizations.models import Organization


def get_organization_tree(organization: Organization) -> Dict[str, Any]:
    """
    Get hierarchical tree representation of organization and its subsidiaries.
    
    Returns nested dict showing parent-child relationships.
    
    Example:
        {
            "id": "uuid",
            "name": "TGI Group",
            "organization_type": "group",
            "subsidiaries": [
                {
                    "id": "uuid",
                    "name": "WACOT Rice",
                    "organization_type": "subsidiary",
                    "subsidiaries": []
                }
            ]
        }
    """
    def build_tree(org: Organization) -> Dict[str, Any]:
        children = org.get_children().filter(is_active=True).values_list(
            'id', 'name', 'entity_type'
        )
        
        child_nodes = [
            build_tree(Organization.objects.get(id=child_id))
            for child_id, _, _ in children
        ]
        
        return {
            "id": str(org.id),
            "name": org.name,
            "entity_type": org.entity_type,
            "entity_type_display": org.get_entity_type_display(),
            "organization_type": org.entity_type,
            "organization_type_display": org.get_entity_type_display(),
            "parent": (
                {"id": str(org.parent.id), "name": org.parent.name}
                if org.parent else None
            ),
            "children": child_nodes,
            "subsidiaries": child_nodes,
        }
    
    return build_tree(organization)


def get_organization_descendants(
    organization: Organization,
    include_self: bool = False,
    entity_types: List[str] = None,
    organization_types: List[str] = None,
) -> QuerySet:
    """
    Get all descendant organizations (children, grandchildren, etc.).
    
    Used for:
    - ESG score aggregation
    - Compliance aggregation
    - Consolidated reporting
    
    Args:
        organization: Parent organization
        include_self: Include parent in results
        entity_types: Filter by specific types (optional)
        organization_types: Backward-compatible alias for entity_types
    
    Returns:
        QuerySet of Organizations
    
    Example:
        descendants = get_organization_descendants(parent_org)
        # Returns: all children and nested children
        
        facilities_only = get_organization_descendants(
            parent_org,
            organization_types=['facility']
        )
    """
    # Get all descendants using model method
    descendants_list = organization.get_descendants(include_self=include_self)
    
    # Convert to QuerySet for efficient filtering
    ids = [org.id for org in descendants_list]
    qs = Organization.objects.filter(id__in=ids, is_active=True)
    
    resolved_entity_types = entity_types or organization_types
    if resolved_entity_types:
        qs = qs.filter(entity_type__in=resolved_entity_types)
    
    return qs


def get_organization_ancestors(
    organization: Organization,
    include_self: bool = False
) -> List[Organization]:
    """
    Get all parent organizations up the hierarchy.
    
    Example:
        ancestors = get_organization_ancestors(subsidiary)
        # Returns: [parent_group, grandparent_group, ...]
    """
    ancestors = []
    if include_self:
        ancestors.append(organization)
    
    current = organization.parent
    while current:
        ancestors.append(current)
        current = current.parent
    
    return ancestors


def get_organization_siblings(organization: Organization) -> QuerySet:
    """
    Get all organizations at same hierarchy level with same parent.
    
    Example:
        siblings = get_organization_siblings(subsidiary)
        # Returns: other subsidiaries of same parent
    """
    if not organization.parent:
        # Root org - get all root orgs
        return Organization.objects.filter(parent__isnull=True, is_active=True)
    
    return organization.parent.children.filter(is_active=True)


def get_organization_depth(organization: Organization) -> int:
    """
    Get depth of organization in hierarchy.
    
    Returns:
        0 = root (no parent)
        1 = child of root
        2 = grandchild of root
        etc.
    """
    return organization.hierarchy_level


def get_organizations_by_level(
    parent: Organization = None,
    level: int = 1,
    entity_type: str = None,
    organization_type: str = None,
) -> QuerySet:
    """
    Get organizations at specific depth/level.
    
    Args:
        parent: Parent org to search within (None = all roots)
        level: Depth level (0=roots, 1=children, 2=grandchildren)
        entity_type: Filter by type (optional)
        organization_type: Backward-compatible alias for entity_type
    
    Returns:
        QuerySet of Organizations at that level
    
    Example:
        # Get all subsidiary companies (direct children of groups)
        subsidiaries = get_organizations_by_level(
            parent=group_org,
            level=1,
            entity_type='subsidiary'
        )
    """
    if parent is None:
        # Root level
        qs = Organization.objects.filter(parent__isnull=True, is_active=True)
    else:
        # Direct children of parent
        qs = Organization.objects.filter(parent=parent, is_active=True)
    
    resolved_entity_type = entity_type or organization_type
    if resolved_entity_type:
        qs = qs.filter(entity_type=resolved_entity_type)
    
    return qs


def get_organization_statistics(organization: Organization) -> Dict[str, Any]:
    """
    Get statistics about organization and its structure.
    
    Returns:
        {
            "total_descendants": 5,
            "direct_children": 2,
            "depth": 2,
            "types": {
                "subsidiary": 2,
                "facility": 3
            }
        }
    """
    descendants = get_organization_descendants(organization, include_self=False)
    
    type_counts = {}
    for org_type, _ in Organization.EntityType.choices:
        count = descendants.filter(entity_type=org_type).count()
        if count > 0:
            type_counts[org_type] = count
    
    return {
        "total_descendants": descendants.count(),
        "direct_children": organization.children.filter(is_active=True).count(),
        "depth": organization.hierarchy_level,
        "hierarchy_depth": organization.hierarchy_level,
        "entity_type": organization.get_entity_type_display(),
        "organization_type": organization.get_organization_type_display(),
        "type_breakdown": type_counts,
    }


def get_subsidiaries(organization: Organization) -> QuerySet:
    """Return direct subsidiary children for a given organization."""
    return organization.children.filter(
        entity_type=Organization.EntityType.SUBSIDIARY,
        is_active=True,
    )


def is_descendant_of(child: Organization, potential_parent: Organization) -> bool:
    """
    Check if child is a descendant of potential_parent.
    
    Useful for:
    - Access control (can user access this org?)
    - Consolidation validation
    
    Example:
        if is_descendant_of(facility, company):
            # Facility's data can be consolidated into company
    """
    ancestors = get_organization_ancestors(child)
    return potential_parent in ancestors


def get_root_organization(organization: Organization) -> Organization:
    """
    Get the top-level parent organization.
    
    Example:
        root = get_root_organization(facility)
        # root = TGI Group Holdings
    """
    ancestors = get_organization_ancestors(organization)
    if ancestors:
        return ancestors[-1]  # Last item is root
    return organization  # Already root
