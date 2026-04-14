"""Organizations API URLs."""
from django.urls import path
from .views import (
    OrganizationOptionsView,
    OrganizationSettingsView,
)
from .views import (
    OrganizationProfileView,
    BusinessUnitListCreateView,
    BusinessUnitDetailView,
    DepartmentListCreateView,
    DepartmentDetailView,
)
from .views import (
    OrganizationHierarchyView,
    SubsidiariesListCreateView,
    SubsidiaryDetailView,
    OrganizationStatisticsView,
)

app_name = "organizations"

urlpatterns = [
    path("options/", OrganizationOptionsView.as_view(), name="options"),
    path("settings/", OrganizationSettingsView.as_view(), name="settings"),
    path("profile/", OrganizationProfileView.as_view(), name="settings-profile"),
    path("business-units/", BusinessUnitListCreateView.as_view(), name="business-units"),
    path("business-units/<uuid:pk>/", BusinessUnitDetailView.as_view(), name="business-unit-detail"),
    path("departments/", DepartmentListCreateView.as_view(), name="departments"),
    path("departments/<uuid:department_id>/", DepartmentDetailView.as_view(), name="department-detail"),
    
    # Enterprise Hierarchy Endpoints (Layer 1)
    # Organization ID is retrieved from X-ORG-ID header (multi-tenant pattern)
    path("hierarchy/", OrganizationHierarchyView.as_view(), name="hierarchy"),
    path("subsidiaries/", SubsidiariesListCreateView.as_view(), name="subsidiaries"),
    path("subsidiaries/<uuid:sub_id>/", SubsidiaryDetailView.as_view(), name="subsidiary-detail"),
    path("statistics/", OrganizationStatisticsView.as_view(), name="statistics"),
    ]