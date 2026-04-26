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
from organizations.selectors.frameworks import get_framework_selection_options
from organizations.services.settings import update_general_settings, update_security_settings
from organizations.services.esg_settings import get_or_create_esg_settings
from organizations.services.framework_selection import update_organization_frameworks
from organizations.services.profile import (
    update_organization_profile,
    create_business_unit,
    update_business_unit,
    delete_business_unit,
)
from organizations.models import Department, Organization, OrganizationESGSettings

from .serializers import (
    OrganizationSettingsDetailSerializer,
    GeneralSettingsUpdateSerializer,
    SecuritySettingsUpdateSerializer,
    OrganizationSettingsSerializer,
    OrganizationESGSettingsSerializer,
    OrganizationFrameworkSelectionSerializer,
    FrameworkSelectionOptionSerializer,
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

        serializer = OrganizationProfileSerializer(data=request.data, partial=True, context={"request": request})
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
            out = OrganizationProfileSerializer(profile, context={"request": request})
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
        out = OrganizationProfileSerializer(profile, context={"request": request})
        return success_response(data=out.data, status=status.HTTP_200_OK)


class OrganizationESGSettingsView(APIView):
    permission_classes = [IsAuthenticated, IsOrgMember, HasCapability]
    required_capability = "org.manage"

    def initial(self, request, *args, **kwargs):
        organization_id = kwargs.get('organization_id')
        if organization_id and not getattr(request, 'organization', None):
            organization = Organization.objects.filter(id=organization_id, is_active=True).first()
            if organization:
                request.organization = organization
        return super().initial(request, *args, **kwargs)

    def _get_organization(self, request, organization_id=None):
        path_org = None
        if organization_id:
            path_org = Organization.objects.filter(id=organization_id, is_active=True).first()
            if path_org:
                request.organization = path_org

        header_org = _get_org(request)
        if path_org and header_org and path_org.id != header_org.id:
            return None
        return path_org or header_org

    def get(self, request, organization_id=None):
        organization = self._get_organization(request, organization_id)
        if not organization:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/not-found",
                    "title": "Organization not found",
                    "detail": "Organization not found or organization context mismatch",
                    "code": "org_not_found",
                },
                status_code=status.HTTP_404_NOT_FOUND,
            )

        serializer = OrganizationESGSettingsSerializer(get_or_create_esg_settings(organization))
        return success_response(data=serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, organization_id=None):
        organization = self._get_organization(request, organization_id)
        if not organization:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/not-found",
                    "title": "Organization not found",
                    "detail": "Organization not found or organization context mismatch",
                    "code": "org_not_found",
                },
                status_code=status.HTTP_404_NOT_FOUND,
            )

        esg_settings = get_or_create_esg_settings(organization)
        serializer = OrganizationESGSettingsSerializer(esg_settings, data=request.data, partial=True)
        if not serializer.is_valid():
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/validation-error",
                    "title": "Validation Error",
                    "detail": "Invalid ESG settings provided",
                    "errors": serializer.errors,
                    "code": "validation_error",
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        updated_settings = serializer.save()
        return success_response(
            data=OrganizationESGSettingsSerializer(updated_settings).data,
            meta={"message": "ESG settings updated successfully"},
            status=status.HTTP_200_OK,
        )


class OrganizationFrameworkSelectionView(APIView):
    permission_classes = [IsAuthenticated, IsOrgMember, HasCapability]
    required_capability = "org.manage"

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

        serializer = FrameworkSelectionOptionSerializer(get_framework_selection_options(organization), many=True)
        return success_response(data={"frameworks": serializer.data}, status=status.HTTP_200_OK)

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

        serializer = OrganizationFrameworkSelectionSerializer(data=request.data)
        if not serializer.is_valid():
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/validation-error",
                    "title": "Validation Error",
                    "detail": "Invalid framework selection payload",
                    "errors": serializer.errors,
                    "code": "validation_error",
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            options = update_organization_frameworks(
                organization=organization,
                updates=serializer.validated_data['frameworks'],
                assigned_by=request.user,
            )
        except DjangoValidationError as exc:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/validation-error",
                    "title": "Validation Error",
                    "detail": str(exc),
                    "code": "validation_error",
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = FrameworkSelectionOptionSerializer(options, many=True)
        return success_response(
            data={"frameworks": response_serializer.data},
            meta={"message": "Framework selection updated successfully"},
            status=status.HTTP_200_OK,
        )


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


# ============================================================================
# ENTERPRISE HIERARCHY VIEWS (Layer 1)
# ============================================================================


class OrganizationHierarchyView(APIView):
    """
    Retrieve the complete hierarchical tree of the user's organization.
    
    GET /api/v1/organizations/hierarchy/
    
    Organization ID is retrieved from X-ORG-ID header.
    Returns the organization and all its subsidiaries in a nested tree structure.
    Includes organization type (GROUP, SUBSIDIARY, FACILITY, DEPARTMENT).
    """
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def get(self, request):
        """Get organization hierarchy tree."""
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
        
        try:
            from organizations.selectors.organization_hierarchy import get_organization_tree
            from organizations.api.serializers import OrganizationTreeSerializer
            
            tree = get_organization_tree(org)
            serializer = OrganizationTreeSerializer(tree)
            return success_response(data=serializer.data)
        except Exception as e:
            logger.error(f"Error fetching hierarchy tree: {str(e)}")
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/internal-error",
                    "title": "Internal Server Error",
                    "detail": "An error occurred while fetching the organization hierarchy",
                },
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SubsidiariesListCreateView(APIView):
    """
    List all direct subsidiaries or create a new subsidiary under the user's organization.
    
    GET /api/v1/organizations/subsidiaries/
    POST /api/v1/organizations/subsidiaries/
    
    Organization ID is retrieved from X-ORG-ID header.
    """
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def check_permissions(self, request):
        if request.method == 'POST':
            self.required_capability = 'org.manage'
            self.permission_classes = [IsAuthenticated, IsOrgMember, HasCapability]
        super().check_permissions(request)
    
    def get(self, request):
        """Get all direct subsidiaries of the organization."""
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
        
        try:
            from organizations.api.serializers import OrganizationDetailSerializer
            from organizations.selectors.organization_hierarchy import get_subsidiaries
            
            # Get direct children only via reverse relationship
            subsidiaries = get_subsidiaries(org)
            serializer = OrganizationDetailSerializer(subsidiaries, many=True)
            return success_response(data=serializer.data)
        except Exception as e:
            logger.error(f"Error fetching subsidiaries: {str(e)}")
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/internal-error",
                    "title": "Internal Server Error",
                    "detail": "An error occurred while fetching subsidiaries",
                },
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    def post(self, request):
        """Create a new subsidiary under the user's organization."""
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
        
        from organizations.api.serializers import CreateSubsidiarySerializer, OrganizationDetailSerializer
        serializer = CreateSubsidiarySerializer(data=request.data)
        
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
            from organizations.services.organization_hierarchy import create_subsidiary
            from organizations.selectors.organization_hierarchy import is_descendant_of

            parent = serializer.validated_data.get('parent') or org
            if parent != org and not is_descendant_of(parent, org):
                return problem_response(
                    {
                        "type": f"{settings.PROBLEM_BASE_URL}/validation-error",
                        "title": "Validation Error",
                        "detail": "Parent organization must belong to your hierarchy",
                    },
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            
            subsidiary = create_subsidiary(
                parent_organization=parent,
                name=serializer.validated_data['name'],
                sector=serializer.validated_data.get('sector'),
                country=serializer.validated_data.get('country'),
                entity_type=serializer.validated_data.get('entity_type', 'subsidiary'),
                company_size=serializer.validated_data.get('company_size'),
                registered_name=serializer.validated_data.get('registered_name'),
                primary_reporting_focus=serializer.validated_data.get('primary_reporting_focus'),
            )
            
            return success_response(
                data=OrganizationDetailSerializer(subsidiary).data,
                status=status.HTTP_201_CREATED
            )
        except (ValueError, DjangoValidationError) as e:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/validation-error",
                    "title": "Validation Error",
                    "detail": str(e),
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Error creating subsidiary: {str(e)}")
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/internal-error",
                    "title": "Internal Server Error",
                    "detail": "An error occurred while creating the subsidiary",
                },
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SubsidiaryDetailView(APIView):
    """
    Retrieve, update, or delete a specific subsidiary organization.
    
    GET /api/v1/organizations/subsidiaries/{sub_id}/
    PATCH /api/v1/organizations/subsidiaries/{sub_id}/
    DELETE /api/v1/organizations/subsidiaries/{sub_id}/
    
    Organization ID is retrieved from X-ORG-ID header.
    """
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def check_permissions(self, request):
        if request.method in ['PATCH', 'DELETE']:
            self.required_capability = 'organization.manage_hierarchy'
            self.permission_classes = [IsAuthenticated, IsOrgMember, HasCapability]
        super().check_permissions(request)
    
    def _get_subsidiary(self, org, subsidiary_id):
        """Get subsidiary by ID and verify it belongs to org."""
        try:
            from organizations.selectors.organization_hierarchy import is_descendant_of
            subsidiary = Organization.objects.get(id=subsidiary_id)
            
            # Check that subsidiary is a descendant of org
            if not is_descendant_of(subsidiary, org):
                return None
            return subsidiary
        except Organization.DoesNotExist:
            return None
    
    def get(self, request, sub_id):
        """Get subsidiary details."""
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
        
        subsidiary = self._get_subsidiary(org, sub_id)
        if not subsidiary:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/not-found",
                    "title": "Subsidiary not found",
                    "detail": "Subsidiary not found or does not belong to your organization",
                },
                status_code=status.HTTP_404_NOT_FOUND,
            )
        
        from organizations.api.serializers import OrganizationDetailSerializer
        serializer = OrganizationDetailSerializer(subsidiary)
        return success_response(data=serializer.data)
    
    def patch(self, request, sub_id):
        """Update subsidiary details."""
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
        
        subsidiary = self._get_subsidiary(org, sub_id)
        if not subsidiary:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/not-found",
                    "title": "Subsidiary not found",
                    "detail": "Subsidiary not found or does not belong to your organization",
                },
                status_code=status.HTTP_404_NOT_FOUND,
            )
        
        from organizations.api.serializers import OrganizationDetailSerializer
        serializer = OrganizationDetailSerializer(subsidiary, data=request.data, partial=True)
        
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
            from organizations.selectors.organization_hierarchy import is_descendant_of

            new_parent = serializer.validated_data.get('parent')
            if new_parent and new_parent != org and not is_descendant_of(new_parent, org):
                return problem_response(
                    {
                        "type": f"{settings.PROBLEM_BASE_URL}/validation-error",
                        "title": "Validation Error",
                        "detail": "Parent organization must belong to your hierarchy",
                    },
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            updated_subsidiary = serializer.save()
            return success_response(data=OrganizationDetailSerializer(updated_subsidiary).data)
        except DjangoValidationError as e:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/validation-error",
                    "title": "Validation Error",
                    "detail": e.message if hasattr(e, 'message') else str(e),
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Error updating subsidiary: {str(e)}")
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/internal-error",
                    "title": "Internal Server Error",
                    "detail": "An error occurred while updating the subsidiary",
                },
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    def delete(self, request, sub_id):
        """Delete a subsidiary."""
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
        
        subsidiary = self._get_subsidiary(org, sub_id)
        if not subsidiary:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/not-found",
                    "title": "Subsidiary not found",
                    "detail": "Subsidiary not found or does not belong to your organization",
                },
                status_code=status.HTTP_404_NOT_FOUND,
            )
        
        try:
            subsidiary.delete()
            return success_response(data={}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting subsidiary: {str(e)}")
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/conflict",
                    "title": "Conflict",
                    "detail": "Cannot delete subsidiary. It may have dependent data.",
                },
                status_code=status.HTTP_409_CONFLICT,
            )


class OrganizationStatisticsView(APIView):
    """
    Retrieve hierarchy statistics for the user's organization.
    
    GET /api/v1/organizations/statistics/
    
    Organization ID is retrieved from X-ORG-ID header.
    Returns metrics like total descendants, direct children, hierarchy depth, 
    and breakdown by organization type.
    """
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def get(self, request):
        """Get organization hierarchy statistics."""
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
        
        try:
            from organizations.selectors.organization_hierarchy import get_organization_statistics
            from organizations.api.serializers import OrganizationStatisticsSerializer
            
            stats = get_organization_statistics(org)
            serializer = OrganizationStatisticsSerializer(stats)
            return success_response(data=serializer.data)
        except Exception as e:
            logger.error(f"Error fetching organization statistics: {str(e)}")
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/internal-error",
                    "title": "Internal Server Error",
                    "detail": "An error occurred while calculating statistics",
                },
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )