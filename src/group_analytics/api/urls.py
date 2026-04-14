"""URL routing for Group Analytics API."""
from django.urls import path
from .views import (
    GroupDashboardView,
    GroupFrameworkReadinessView,
    GroupESGScoreView,
    GroupGapsView,
    GroupRecommendationsView,
    SubsidiaryRankingView,
    SubsidiaryComparisonView,
    PortfolioSummaryView,
)

app_name = 'group_analytics'

urlpatterns = [
    path('dashboard/', GroupDashboardView.as_view(), name='dashboard'),
    path('esg-score/', GroupESGScoreView.as_view(), name='esg_score'),
    path('framework-readiness/', GroupFrameworkReadinessView.as_view(), name='framework_readiness'),
    path('top-gaps/', GroupGapsView.as_view(), name='top_gaps'),
    path('recommendations/', GroupRecommendationsView.as_view(), name='recommendations'),
    path('subsidiaries/', SubsidiaryRankingView.as_view(), name='subsidiaries'),
    path('comparison/', SubsidiaryComparisonView.as_view(), name='comparison'),
    path('portfolio-summary/', PortfolioSummaryView.as_view(), name='portfolio_summary'),
]
