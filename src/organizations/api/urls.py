"""Organizations API URLs."""
from django.urls import path
from .views import OrganizationOptionsView

app_name = "organizations"

urlpatterns = [
    path("options/", OrganizationOptionsView.as_view(), name="options"),
]
