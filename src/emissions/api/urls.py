from django.urls import path
from .views import ScopeEmissionsAPIView

urlpatterns = [
	path('scope/<str:scope>/', ScopeEmissionsAPIView.as_view(), name='emissions-scope'),
]

