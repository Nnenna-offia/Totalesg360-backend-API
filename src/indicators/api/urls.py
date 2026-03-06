from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IndicatorViewSet

router = DefaultRouter()
router.register(r'', IndicatorViewSet, basename='indicator')

urlpatterns = [
    path('', include(router.urls)),
]
