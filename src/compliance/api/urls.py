from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .framework_views import (
    FrameworkRequirementViewSet,
    IndicatorFrameworkMappingViewSet,
    OrganizationFrameworkViewSet,
    FrameworkListViewSet,
)
from .compliance_intelligence_views import (
    FrameworkReadinessViewSet,
    ComplianceGapPriorityViewSet,
    ComplianceRecommendationViewSet,
    ComplianceIntelligenceDashboardViewSet,
)

# DRF Router for ViewSets
router = DefaultRouter()
router.register(r'framework-requirements', FrameworkRequirementViewSet, basename='framework-requirement')
router.register(r'indicator-mappings', IndicatorFrameworkMappingViewSet, basename='indicator-mapping')
router.register(r'organization-frameworks', OrganizationFrameworkViewSet, basename='organization-framework')
router.register(r'frameworks', FrameworkListViewSet, basename='framework-list')

# Layer 5 - Compliance Intelligence Routes
router.register(r'readiness', FrameworkReadinessViewSet, basename='readiness')
router.register(r'gaps', ComplianceGapPriorityViewSet, basename='gap-priority')
router.register(r'recommendations', ComplianceRecommendationViewSet, basename='recommendation')
router.register(r'intelligence', ComplianceIntelligenceDashboardViewSet, basename='intelligence')

urlpatterns = [
    # Legacy compliance endpoints
    path('organization', views.OrganizationComplianceView.as_view(), name='compliance-organization'),
    path('framework/<uuid:framework_id>', views.FrameworkComplianceView.as_view(), name='compliance-framework'),
    path('missing', views.MissingIndicatorsView.as_view(), name='compliance-missing'),
    
    # Framework mapping router
    path('', include(router.urls)),
]