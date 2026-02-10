"""Metadata and options API views."""
from rest_framework.views import APIView
from rest_framework import status
from django_countries import countries

from common.api import success_response
from organizations.models import Organization


class SignupOptionsView(APIView):
    """Get available options for signup form.
    
    GET /api/v1/signup-options/
    
    Returns country list, sector choices, and primary reporting focus options
    for populating signup form dropdowns.
    
    Response: 200 OK
    {
        "success": true,
        "data": {
            "countries": [
                {"code": "NG", "name": "Nigeria"},
                {"code": "US", "name": "United States"},
                ...
            ],
            "sectors": [
                {"value": "manufacturing", "label": "Manufacturing"},
                {"value": "oil_gas", "label": "Oil & Gas"},
                {"value": "finance", "label": "Finance"}
            ],
            "primary_reporting_focus": [
                {"value": "NIGERIA", "label": "Nigeria Regulators Only"},
                {"value": "INTERNATIONAL", "label": "International Frameworks Only"},
                {"value": "HYBRID", "label": "Nigeria + International (Hybrid)"}
            ]
        }
    }
    """
    
    permission_classes = []  # Public endpoint
    authentication_classes = []
    
    def get(self, request):
        # Get countries from django-countries
        countries_list = [
            {"code": code, "name": name}
            for code, name in countries
        ]
        
        # Get sectors from Organization model choices
        sectors_list = [
            {"value": value, "label": label}
            for value, label in Organization._meta.get_field("sector").choices
        ]
        
        # Get primary reporting focus from Organization model choices
        reporting_focus_list = [
            {"value": value, "label": label}
            for value, label in Organization.PrimaryReportingFocus.choices
        ]
        
        data = {
            "countries": countries_list,
            "sectors": sectors_list,
            "primary_reporting_focus": reporting_focus_list,
        }
        
        return success_response(data=data, status=status.HTTP_200_OK)
