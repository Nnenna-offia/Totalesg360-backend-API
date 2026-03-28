"""Selectors for department queries."""
from organizations.models import Department


def get_organization_departments(organization, active_only=True):
    """
    Get all departments for an organization.
    
    Args:
        organization: Organization instance
        active_only: If True, only return active departments (default: True)
    
    Returns:
        QuerySet of Department objects
    """
    qs = organization.departments.all()
    
    if active_only:
        qs = qs.filter(is_active=True)
    
    return qs.order_by('name')


def get_department_by_id(organization, department_id):
    """
    Get a specific department by ID.
    
    Args:
        organization: Organization instance
        department_id: Department UUID
    
    Returns:
        Department instance or None
    """
    return organization.departments.filter(id=department_id).first()


def get_department_by_name(organization, name):
    """
    Get a department by name.
    
    Args:
        organization: Organization instance
        name: Department name
    
    Returns:
        Department instance or None
    """
    return organization.departments.filter(name=name).first()
