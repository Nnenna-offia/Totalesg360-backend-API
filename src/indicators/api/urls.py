from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IndicatorViewSet, EmissionIndicatorValueAPIView, OrganizationActiveIndicatorListAPIView

router = DefaultRouter()
router.register(r'', IndicatorViewSet, basename='indicator')

urlpatterns = [
	path('active/', OrganizationActiveIndicatorListAPIView.as_view(), name='indicator-active'),
    path('', include(router.urls)),
    path('emission/<str:code>/', EmissionIndicatorValueAPIView.as_view(), name='indicator-emission-value'),
]
