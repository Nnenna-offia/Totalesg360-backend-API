"""Organizations API URLs."""
from django.urls import path
from .views import (
    OrganizationOptionsView,
    OrganizationSettingsView,
    GeneralSettingsUpdateView,
    SecuritySettingsUpdateView
)
from .views import (
    OrganizationProfileView,
    BusinessUnitListCreateView,
    BusinessUnitDetailView,
)

app_name = "organizations"

urlpatterns = [
    path("options/", OrganizationOptionsView.as_view(), name="options"),
    path("settings/", OrganizationSettingsView.as_view(), name="settings"),
    path("settings/general/", GeneralSettingsUpdateView.as_view(), name="settings-general"),
    path("settings/security/", SecuritySettingsUpdateView.as_view(), name="settings-security"),
    path("profile/", OrganizationProfileView.as_view(), name="settings-profile"),
    path("business-units/", BusinessUnitListCreateView.as_view(), name="business-units"),
    path("business-units/<uuid:pk>/", BusinessUnitDetailView.as_view(), name="business-unit-detail"),
]
