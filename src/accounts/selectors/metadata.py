"""Selectors for fetching metadata and options."""
from django_countries import countries


def get_countries_list():
    """
    Fetch list of all countries from django-countries package.
    
    Returns:
        list: List of dicts with code and name keys
        
    Example:
        [
            {"code": "NG", "name": "Nigeria"},
            {"code": "US", "name": "United States"},
            ...
        ]
    """
    return [
        {"code": code, "name": name}
        for code, name in countries
    ]
