from django.urls import path
from .views import (
	SubmitIndicatorAPIView,
	PeriodSubmissionsAPIView,
	ReportingPeriodListCreateAPIView,
	FinalizePeriodAPIView,
	ApproveSubmissionAPIView,
)

urlpatterns = [
	path('submit/', SubmitIndicatorAPIView.as_view(), name='submit-indicator'),
	path('periods/', ReportingPeriodListCreateAPIView.as_view(), name='periods-list-create'),
	path('periods/<uuid:period_id>/', PeriodSubmissionsAPIView.as_view(), name='period-submissions'),
	path('periods/<uuid:period_id>/finalize/', FinalizePeriodAPIView.as_view(), name='finalize-period'),
	path('<uuid:submission_id>/approve/', ApproveSubmissionAPIView.as_view(), name='approve-submission'),
]
