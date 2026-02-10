"""Selectors for fetching organization metadata and options."""
from organizations.models import Organization


def get_sectors_list():
    """
    Fetch list of available sectors from Organization model.
    
    Returns:
        list: List of dicts with value and label keys
        
    Example:
        [
            {"value": "manufacturing", "label": "Manufacturing"},
            {"value": "oil_gas", "label": "Oil & Gas"},
            {"value": "finance", "label": "Finance"}
        ]
    """
    return [
        {"value": value, "label": label}
        for value, label in Organization._meta.get_field("sector").choices
    ]


def get_primary_reporting_focus_list():
    """
    Fetch list of primary reporting focus options from Organization model.
    
    Returns:
        list: List of dicts with value and label keys
        
    Example:
        [
            {"value": "NIGERIA", "label": "Nigeria Regulators Only"},
            {"value": "INTERNATIONAL", "label": "International Frameworks Only"},
            {"value": "HYBRID", "label": "Nigeria + International (Hybrid)"}
        ]
    """
    return [
        {"value": value, "label": label}
        for value, label in Organization.PrimaryReportingFocus.choices
    ]
