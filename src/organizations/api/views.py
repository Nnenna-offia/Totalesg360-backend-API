"""Organizations API views."""
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError

from common.api import success_response, problem_response
from common.permissions import HasCapability, IsOrgMember, _get_org
from organizations.selectors.metadata import (
    get_sectors_list,
    get_primary_reporting_focus_list,
)
from organizations.selectors.settings import get_organization_settings, get_organization_with_settings
from organizations.selectors.department import get_organization_departments, get_department_by_id
from organizations.services.settings import update_general_settings, update_security_settings
from organizations.services.profile import (
    update_organization_profile,
    create_business_unit,
    update_business_unit,
    delete_business_unit,
)
from organizations.models import Department

from .serializers import (
    OrganizationSettingsDetailSerializer,
    GeneralSettingsUpdateSerializer,
    SecuritySettingsUpdateSerializer,
    OrganizationSettingsSerializer
)
from .serializers import OrganizationProfileSerializer, BusinessUnitSerializer
from organizations.models import BusinessUnit, OrganizationProfile


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


class OrganizationSettingsView(APIView):
    """
    Get organization settings with all related data.
    
    GET /api/v1/organizations/settings/
    
    Headers:
        X-ORG-ID: Organization UUID
    
    Returns:
        Organization details, settings, departments, and frameworks.
        
    Response: 200 OK
    {
        "success": true,
        "data": {
            "organization": {...},
            "settings": {...},
            "departments": [...],
            "frameworks": [...]
        }
    }
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        organization = _get_org(request)
        
        if not organization:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/not-found",
                    "title": "Organization not found",
                    "detail": "Organization not found or X-ORG-ID header missing",
                    "code": "org_not_found",
                },
                status_code=status.HTTP_404_NOT_FOUND,
            )
        
        settings_data = get_organization_settings(str(organization.id))
        
        if not settings_data:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/not-found",
                    "title": "Organization settings not found",
                    "detail": "Organization settings not found",
                    "code": "org_settings_not_found",
                },
                status_code=status.HTTP_404_NOT_FOUND,
            )
        
        serializer = OrganizationSettingsDetailSerializer(settings_data)
        return success_response(data=serializer.data, status=status.HTTP_200_OK)


class GeneralSettingsUpdateView(APIView):
    """
    Update general settings for an organization.
    
    PATCH /api/v1/organizations/settings/general/
    
    Headers:
        X-ORG-ID: Organization UUID
    
    Request Body:
    {
        "system_language": "en",
        "timezone": "Africa/Lagos",
        "currency": "NGN",
        "date_format": "DD/MM/YYYY",
        "admin_theme": "light",
        "notifications_enabled": true,
        "system_update_frequency": "daily",
        "export_formats": ["pdf", "xlsx", "csv"]
    }
    
    Response: 200 OK
    {
        "success": true,
        "data": {...updated settings...}
    }
    """
    
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = "org.manage"
    
    def patch(self, request):
        organization = _get_org(request)
        
        if not organization:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/not-found",
                    "title": "Organization not found",
                    "detail": "Organization not found or X-ORG-ID header missing",
                    "code": "org_not_found",
                },
                status_code=status.HTTP_404_NOT_FOUND,
            )
        
        organization = get_organization_with_settings(str(organization.id))
        
        if not organization:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/not-found",
                    "title": "Organization not found",
                    "detail": "Organization not found",
                    "code": "org_not_found",
                },
                status_code=status.HTTP_404_NOT_FOUND,
            )
        
        serializer = GeneralSettingsUpdateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/validation-error",
                    "title": "Validation Error",
                    "detail": "Invalid data provided",
                    "errors": serializer.errors,
                    "code": "validation_error",
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            updated_settings = update_general_settings(
                organization=organization,
                **serializer.validated_data
            )
            
            settings_serializer = OrganizationSettingsSerializer(updated_settings)
            return success_response(
                data=settings_serializer.data,
                meta={"message": "General settings updated successfully"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/update-failed",
                    "title": "Update Failed",
                    "detail": str(e),
                    "code": "update_failed",
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )


class SecuritySettingsUpdateView(APIView):
    """
    Update security settings for an organization.
    
    PATCH /api/v1/organizations/settings/security/
    
    Headers:
        X-ORG-ID: Organization UUID
    
    Request Body:
    {
        "security_checks_frequency": "daily",
        "require_2fa": true,
        "encrypt_stored_data": true,
        "encryption_method": "AES-256"
    }
    
    Response: 200 OK
    {
        "success": true,
        "data": {...updated settings...}
    }
    """
    
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = "org.manage"
    
    def patch(self, request):
        organization = _get_org(request)
        
        if not organization:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/not-found",
                    "title": "Organization not found",
                    "detail": "Organization not found or X-ORG-ID header missing",
                    "code": "org_not_found",
                },
                status_code=status.HTTP_404_NOT_FOUND,
            )
        
        organization = get_organization_with_settings(str(organization.id))
        
        if not organization:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/not-found",
                    "title": "Organization not found",
                    "detail": "Organization not found",
                    "code": "org_not_found",
                },
                status_code=status.HTTP_404_NOT_FOUND,
            )
        
        serializer = SecuritySettingsUpdateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/validation-error",
                    "title": "Validation Error",
                    "detail": "Invalid data provided",
                    "errors": serializer.errors,
                    "code": "validation_error",
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            updated_settings = update_security_settings(
                organization=organization,
                **serializer.validated_data
            )
            
            settings_serializer = OrganizationSettingsSerializer(updated_settings)
            return success_response(
                data=settings_serializer.data,
                meta={"message": "Security settings updated successfully"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/update-failed",
                    "title": "Update Failed",
                    "detail": str(e),
                    "code": "update_failed",
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )


class OrganizationProfileView(APIView):
    """Retrieve or update the organization's company profile (logo, CAC, locations)."""

    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = "org.manage"

    def patch(self, request):
        org = _get_org(request)
        if not org:
            return problem_response({
                "type": f"{settings.PROBLEM_BASE_URL}/not-found",
                "title": "Organization not found",
                "detail": "Organization not found or X-ORG-ID header missing",
                "code": "org_not_found",
            }, status_code=status.HTTP_404_NOT_FOUND)

        serializer = OrganizationProfileSerializer(data=request.data)
        if not serializer.is_valid():
            return problem_response({
                "type": f"{settings.PROBLEM_BASE_URL}/validation-error",
                "title": "Validation Error",
                "detail": "Invalid data provided",
                "errors": serializer.errors,
                "code": "validation_error",
            }, status_code=status.HTTP_400_BAD_REQUEST)

        try:
            profile = update_organization_profile(org, **serializer.validated_data)
            out = OrganizationProfileSerializer(profile)
            return success_response(data=out.data, meta={"message": "Profile updated"}, status=status.HTTP_200_OK)
        except Exception as e:
            return problem_response({
                "type": f"{settings.PROBLEM_BASE_URL}/update-failed",
                "title": "Update Failed",
                "detail": str(e),
                "code": "update_failed",
            }, status_code=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        org = _get_org(request)
        if not org:
            return problem_response({
                "type": f"{settings.PROBLEM_BASE_URL}/not-found",
                "title": "Organization not found",
                "detail": "Organization not found or X-ORG-ID header missing",
                "code": "org_not_found",
            }, status_code=status.HTTP_404_NOT_FOUND)

        profile, _ = OrganizationProfile.objects.get_or_create(organization=org)
        out = OrganizationProfileSerializer(profile)
        return success_response(data=out.data, status=status.HTTP_200_OK)


class BusinessUnitListCreateView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = "org.manage"

    def get(self, request):
        org = _get_org(request)
        if not org:
            return problem_response({"type": f"{settings.PROBLEM_BASE_URL}/not-found","title": "Org not found","detail": "Organization not found","code": "org_not_found"}, status_code=status.HTTP_404_NOT_FOUND)
        units = org.business_units.all()
        serializer = BusinessUnitSerializer(units, many=True)
        return success_response(data=serializer.data)

    def post(self, request):
        org = _get_org(request)
        if not org:
            return problem_response({"type": f"{settings.PROBLEM_BASE_URL}/not-found","title": "Org not found","detail": "Organization not found","code": "org_not_found"}, status_code=status.HTTP_404_NOT_FOUND)
        serializer = BusinessUnitSerializer(data=request.data)
        if not serializer.is_valid():
            return problem_response({"type": f"{settings.PROBLEM_BASE_URL}/validation-error","title": "Validation Error","detail": "Invalid data","errors": serializer.errors,"code": "validation_error"}, status_code=status.HTTP_400_BAD_REQUEST)
        bu = create_business_unit(org, name=serializer.validated_data['name'])
        out = BusinessUnitSerializer(bu)
        return success_response(data=out.data, status=status.HTTP_201_CREATED)


class BusinessUnitDetailView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = "org.manage"

    def get_object(self, org, pk):
        try:
            return org.business_units.get(id=pk)
        except BusinessUnit.DoesNotExist:
            return None

    def get(self, request, pk):
        org = _get_org(request)
        if not org:
            return problem_response({"type": f"{settings.PROBLEM_BASE_URL}/not-found","title": "Org not found","detail": "Organization not found","code": "org_not_found"}, status_code=status.HTTP_404_NOT_FOUND)
        bu = self.get_object(org, pk)
        if not bu:
            return problem_response({"type": f"{settings.PROBLEM_BASE_URL}/not-found","title": "Business unit not found","detail": "Business unit not found","code": "bu_not_found"}, status_code=status.HTTP_404_NOT_FOUND)
        return success_response(data=BusinessUnitSerializer(bu).data)

    def patch(self, request, pk):
        org = _get_org(request)
        if not org:
            return problem_response({"type": f"{settings.PROBLEM_BASE_URL}/not-found","title": "Org not found","detail": "Organization not found","code": "org_not_found"}, status_code=status.HTTP_404_NOT_FOUND)
        bu = self.get_object(org, pk)
        if not bu:
            return problem_response({"type": f"{settings.PROBLEM_BASE_URL}/not-found","title": "Business unit not found","detail": "Business unit not found","code": "bu_not_found"}, status_code=status.HTTP_404_NOT_FOUND)
        serializer = BusinessUnitSerializer(data=request.data)
        if not serializer.is_valid():
            return problem_response({"type": f"{settings.PROBLEM_BASE_URL}/validation-error","title": "Validation Error","detail": "Invalid data","errors": serializer.errors,"code": "validation_error"}, status_code=status.HTTP_400_BAD_REQUEST)
        bu = update_business_unit(bu, name=serializer.validated_data['name'])
        return success_response(data=BusinessUnitSerializer(bu).data)

    def delete(self, request, pk):
        org = _get_org(request)
        if not org:
            return problem_response({"type": f"{settings.PROBLEM_BASE_URL}/not-found","title": "Org not found","detail": "Organization not found","code": "org_not_found"}, status_code=status.HTTP_404_NOT_FOUND)
        bu = self.get_object(org, pk)
        if not bu:
            return problem_response({"type": f"{settings.PROBLEM_BASE_URL}/not-found","title": "Business unit not found","detail": "Business unit not found","code": "bu_not_found"}, status_code=status.HTTP_404_NOT_FOUND)
        delete_business_unit(bu)
        return success_response(data={})

class DepartmentListCreateView(APIView):
    """
    List and create departments for an organization.
    
    GET /api/v1/organizations/departments/ - List departments
    POST /api/v1/organizations/departments/ - Create department
    """
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def check_permissions(self, request):
        # For POST, add capability check
        if request.method == 'POST':
            self.required_capability = 'department.manage'
            self.permission_classes = [IsAuthenticated, IsOrgMember, HasCapability]
        else:
            self.permission_classes = [IsAuthenticated, IsOrgMember]
        super().check_permissions(request)
    
    def get(self, request):
        org = _get_org(request)
        if not org:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/not-found",
                    "title": "Organization not found",
                    "detail": "Organization not found or X-ORG-ID header missing",
                },
                status_code=status.HTTP_404_NOT_FOUND,
            )
        
        departments = get_organization_departments(org, active_only=True)
        from organizations.api.serializers import DepartmentSerializer
        serializer = DepartmentSerializer(departments, many=True)
        return success_response(data=serializer.data)
    
    def post(self, request):
        org = _get_org(request)
        if not org:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/not-found",
                    "title": "Organization not found",
                    "detail": "Organization not found or X-ORG-ID header missing",
                },
                status_code=status.HTTP_404_NOT_FOUND,
            )
        
        from organizations.api.serializers import DepartmentSerializer
        serializer = DepartmentSerializer(data=request.data)
        
        if not serializer.is_valid():
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/validation-error",
                    "title": "Validation Error",
                    "detail": serializer.errors,
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            dept = serializer.save(organization=org)
            return success_response(
                data=DepartmentSerializer(dept).data,
                status=status.HTTP_201_CREATED
            )
        except IntegrityError as e:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/duplicate-resource",
                    "title": "Duplicate Department",
                    "detail": f"A department with this name already exists in your organization",
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )


class DepartmentDetailView(APIView):
    """
    Retrieve, update, and delete a specific department.
    
    GET /api/v1/organizations/departments/{id}/
    PATCH /api/v1/organizations/departments/{id}/
    DELETE /api/v1/organizations/departments/{id}/
    """
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def get_object(self, org, department_id):
        return get_department_by_id(org, department_id)
    
    def check_permissions(self, request):
        # For PATCH and DELETE, add capability check
        if request.method in ['PATCH', 'DELETE']:
            self.required_capability = 'department.manage'
            self.permission_classes = [IsAuthenticated, IsOrgMember, HasCapability]
        else:
            self.permission_classes = [IsAuthenticated, IsOrgMember]
        super().check_permissions(request)
    
    def get(self, request, department_id):
        org = _get_org(request)
        if not org:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/not-found",
                    "title": "Organization not found",
                    "detail": "Organization not found",
                },
                status_code=status.HTTP_404_NOT_FOUND,
            )
        
        dept = self.get_object(org, department_id)
        if not dept:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/not-found",
                    "title": "Department not found",
                    "detail": "Department not found",
                },
                status_code=status.HTTP_404_NOT_FOUND,
            )
        
        from organizations.api.serializers import DepartmentSerializer
        serializer = DepartmentSerializer(dept)
        return success_response(data=serializer.data)
    
    def patch(self, request, department_id):
        org = _get_org(request)
        if not org:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/not-found",
                    "title": "Organization not found",
                    "detail": "Organization not found",
                },
                status_code=status.HTTP_404_NOT_FOUND,
            )
        
        dept = self.get_object(org, department_id)
        if not dept:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/not-found",
                    "title": "Department not found",
                    "detail": "Department not found",
                },
                status_code=status.HTTP_404_NOT_FOUND,
            )
        
        from organizations.api.serializers import DepartmentSerializer
        serializer = DepartmentSerializer(dept, data=request.data, partial=True)
        
        if not serializer.is_valid():
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/validation-error",
                    "title": "Validation Error",
                    "detail": serializer.errors,
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            updated_dept = serializer.save()
            return success_response(data=DepartmentSerializer(updated_dept).data)
        except IntegrityError:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/duplicate-resource",
                    "title": "Duplicate Department",
                    "detail": "A department with this name already exists in your organization",
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )
    
    def delete(self, request, department_id):
        org = _get_org(request)
        if not org:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/not-found",
                    "title": "Organization not found",
                    "detail": "Organization not found",
                },
                status_code=status.HTTP_404_NOT_FOUND,
            )
        
        dept = self.get_object(org, department_id)
        if not dept:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/not-found",
                    "title": "Department not found",
                    "detail": "Department not found",
                },
                status_code=status.HTTP_404_NOT_FOUND,
            )
        
        try:
            dept.delete()
            return success_response(data={}, status=status.HTTP_204_NO_CONTENT)
        except DjangoValidationError as e:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/conflict",
                    "title": "Conflict",
                    "detail": str(e),
                },
                status_code=status.HTTP_409_CONFLICT,
            )