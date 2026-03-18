from django.urls import path

from .views import (
	ActivitySubmissionCreateAPIView,
	ActivityTypeListCreateAPIView,
	ActivityTypeDetailAPIView,
	ScopeListCreateAPIView,
	ScopeDetailAPIView,
	ActivitySubmissionListAPIView,
	ActivitySubmissionDetailAPIView,
	ActivitySubmissionsByPeriodAPIView,
	ActivityAnalyticsSummaryAPIView,
	ActivityAnalyticsTrendsAPIView,
	ActivityAnalyticsByFacilityAPIView,
	ActivityAnalyticsComparisonAPIView,
	ActivitySubmissionBulkCreateAPIView,
	ActivitySubmissionBulkDeleteAPIView,
)

urlpatterns = [
	# Activity Types
	path('types/', ActivityTypeListCreateAPIView.as_view(), name='activity-types-list'),
	path('types/<uuid:pk>/', ActivityTypeDetailAPIView.as_view(), name='activity-types-detail'),
	
	# Scopes
	path('scopes/', ScopeListCreateAPIView.as_view(), name='activity-scopes-list'),
	path('scopes/<uuid:pk>/', ScopeDetailAPIView.as_view(), name='activity-scopes-detail'),
	
	# Activity Submissions (create endpoint kept for backward compatibility)
	path('submissions/', ActivitySubmissionCreateAPIView.as_view(), name='activities-submissions-create'),
	path('submissions/list/', ActivitySubmissionListAPIView.as_view(), name='activities-submissions-list'),
	path('submissions/<uuid:pk>/', ActivitySubmissionDetailAPIView.as_view(), name='activities-submissions-detail'),
	path('submissions/period/<uuid:period_id>/', ActivitySubmissionsByPeriodAPIView.as_view(), name='activities-submissions-by-period'),
	
	# Bulk Operations
	path('submissions/bulk/create/', ActivitySubmissionBulkCreateAPIView.as_view(), name='activities-submissions-bulk-create'),
	path('submissions/bulk/delete/', ActivitySubmissionBulkDeleteAPIView.as_view(), name='activities-submissions-bulk-delete'),
	
	# Analytics
	path('analytics/summary/', ActivityAnalyticsSummaryAPIView.as_view(), name='activities-analytics-summary'),
	path('analytics/trends/', ActivityAnalyticsTrendsAPIView.as_view(), name='activities-analytics-trends'),
	path('analytics/by-facility/', ActivityAnalyticsByFacilityAPIView.as_view(), name='activities-analytics-by-facility'),
	path('analytics/comparison/', ActivityAnalyticsComparisonAPIView.as_view(), name='activities-analytics-comparison'),
]

