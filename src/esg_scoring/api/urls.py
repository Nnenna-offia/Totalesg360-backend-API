"""ESG Scoring API URL Routing."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from esg_scoring.api.views import (
    ESGScoreViewSet,
    IndicatorScoreViewSet,
    PillarScoreViewSet,
)

router = DefaultRouter()
router.register(r'scores', ESGScoreViewSet, basename='esg-score')
router.register(r'indicators', IndicatorScoreViewSet, basename='indicator-score')
router.register(r'pillars', PillarScoreViewSet, basename='pillar-score')

urlpatterns = [
    path('', include(router.urls)),
]
