from django.urls import path
from .views import (
	SubmitIndicatorAPIView,
	PeriodSubmissionsAPIView,
	PeriodIndicatorValuesAPIView,
	ReportingPeriodListCreateAPIView,
	FinalizePeriodAPIView,
	ApproveSubmissionAPIView,
    ActiveReportingPeriodAPIView,
)

urlpatterns = [
	path('submit/', SubmitIndicatorAPIView.as_view(), name='submit-indicator'),
	path('periods/', ReportingPeriodListCreateAPIView.as_view(), name='periods-list-create'),
    path('periods/active/', ActiveReportingPeriodAPIView.as_view(), name='periods-active'),
	path('periods/<uuid:period_id>/', PeriodSubmissionsAPIView.as_view(), name='period-submissions'),
	path('periods/<uuid:period_id>/values/', PeriodIndicatorValuesAPIView.as_view(), name='period-indicator-values'),
	path('periods/<uuid:period_id>/finalize/', FinalizePeriodAPIView.as_view(), name='finalize-period'),
	path('<uuid:submission_id>/approve/', ApproveSubmissionAPIView.as_view(), name='approve-submission'),
]
