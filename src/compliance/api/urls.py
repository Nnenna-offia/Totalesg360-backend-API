from django.urls import path
from . import views

urlpatterns = [
    path('organization', views.OrganizationComplianceView.as_view(), name='compliance-organization'),
    path('framework/<uuid:framework_id>', views.FrameworkComplianceView.as_view(), name='compliance-framework'),
    path('missing', views.MissingIndicatorsView.as_view(), name='compliance-missing'),
]

