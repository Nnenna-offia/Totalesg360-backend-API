from django.urls import path
from .views import (
    DashboardSummaryView,
    DashboardEnvironmentalView,
    DashboardSocialView,
    DashboardGovernanceView,
    DashboardTargetsView,
    DashboardTrendsView,
)

urlpatterns = [
    path('summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('environmental/', DashboardEnvironmentalView.as_view(), name='dashboard-environmental'),
    path('social/', DashboardSocialView.as_view(), name='dashboard-social'),
    path('governance/', DashboardGovernanceView.as_view(), name='dashboard-governance'),
    path('targets/', DashboardTargetsView.as_view(), name='dashboard-targets'),
    path('trends/', DashboardTrendsView.as_view(), name='dashboard-trends'),
]
