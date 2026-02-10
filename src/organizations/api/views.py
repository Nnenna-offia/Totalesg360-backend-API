"""Organizations API views."""
from rest_framework.views import APIView
from rest_framework import status

from common.api import success_response
from organizations.selectors.metadata import (
    get_sectors_list,
    get_primary_reporting_focus_list,
)


class OrganizationOptionsView(APIView):
    """
    Get available options for organization-related forms.
    
    GET /api/v1/organizations/options/
    
    Returns:
        Sectors and primary reporting focus options for dropdowns.
        
    Response: 200 OK
    {
        "success": true,
        "data": {
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
        data = {
            "sectors": get_sectors_list(),
            "primary_reporting_focus": get_primary_reporting_focus_list(),
        }
        
        return success_response(data=data, status=status.HTTP_200_OK)
