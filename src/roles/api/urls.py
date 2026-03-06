from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CapabilityViewSet, RoleViewSet

router = DefaultRouter()
router.register(r'capabilities', CapabilityViewSet, basename='capability')
router.register(r'', RoleViewSet, basename='role')

urlpatterns = [
    path('', include(router.urls)),
]
