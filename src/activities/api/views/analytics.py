from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Sum, Avg, Q
from django.db.models.functions import TruncMonth

from common.api import success_response, problem_response
from common.permissions import HasCapability
from accounts.selectors.org_context import get_org_and_membership
from submissions.models.activity_submission import ActivitySubmission
from activities.models.activity_type import ActivityType


class ActivityAnalyticsSummaryAPIView(APIView):
	"""Get overall activity submission analytics for the organization."""
	permission_classes = [IsAuthenticated, HasCapability]
	required_capability = 'submit_activity'
	
	def get(self, request):
		org, membership = get_org_and_membership(request=request)
		
		# Get filters
		start_date = request.query_params.get('start_date')
		end_date = request.query_params.get('end_date')
		scope = request.query_params.get('scope')
		
		queryset = ActivitySubmission.objects.filter(organization=org)
		
		if start_date:
			queryset = queryset.filter(created_at__gte=start_date)
		if end_date:
			queryset = queryset.filter(created_at__lte=end_date)
		if scope:
			queryset = queryset.filter(activity_type__scope__code=scope)
		
		# Overall stats
		total_stats = queryset.aggregate(
			total_submissions=Count('id'),
			total_value=Sum('value'),
			avg_value=Avg('value'),
			unique_activity_types=Count('activity_type', distinct=True),
			unique_facilities=Count('facility', distinct=True)
		)
		
		# By activity type
		by_activity_type = queryset.values(
			'activity_type__id',
			'activity_type__name',
			'activity_type__unit',
			'activity_type__scope__code'
		).annotate(
			submission_count=Count('id'),
			total_value=Sum('value'),
			avg_value=Avg('value')
		).order_by('-total_value')[:10]
		
		# By scope
		by_scope = queryset.values(
			'activity_type__scope__code',
			'activity_type__scope__name'
		).annotate(
			submission_count=Count('id'),
			total_value=Sum('value')
		).order_by('activity_type__scope__code')
		
		# By facility (top 10)
		by_facility = queryset.filter(
			facility__isnull=False
		).values(
			'facility__id',
			'facility__name'
		).annotate(
			submission_count=Count('id'),
			total_value=Sum('value')
		).order_by('-submission_count')[:10]
		
		return success_response(data={
			'overall': {
				'total_submissions': total_stats['total_submissions'],
				'total_value': float(total_stats['total_value'] or 0),
				'avg_value': float(total_stats['avg_value'] or 0),
				'unique_activity_types': total_stats['unique_activity_types'],
				'unique_facilities': total_stats['unique_facilities']
			},
			'by_activity_type': list(by_activity_type),
			'by_scope': list(by_scope),
			'by_facility': list(by_facility)
		})


class ActivityAnalyticsTrendsAPIView(APIView):
	"""Get time-series trends for activity submissions."""
	permission_classes = [IsAuthenticated, HasCapability]
	required_capability = 'submit_activity'
	
	def get(self, request):
		org, membership = get_org_and_membership(request=request)
		
		# Get filters
		activity_type_id = request.query_params.get('activity_type_id')
		scope = request.query_params.get('scope')
		facility_id = request.query_params.get('facility_id')
		
		queryset = ActivitySubmission.objects.filter(organization=org)
		
		if activity_type_id:
			queryset = queryset.filter(activity_type_id=activity_type_id)
		if scope:
			queryset = queryset.filter(activity_type__scope__code=scope)
		if facility_id:
			queryset = queryset.filter(facility_id=facility_id)
		
		# Group by month
		monthly_trends = queryset.annotate(
			month=TruncMonth('created_at')
		).values('month').annotate(
			submission_count=Count('id'),
			total_value=Sum('value'),
			avg_value=Avg('value')
		).order_by('month')
		
		# Format for output
		trends_data = [
			{
				'month': item['month'].strftime('%Y-%m'),
				'submission_count': item['submission_count'],
				'total_value': float(item['total_value'] or 0),
				'avg_value': float(item['avg_value'] or 0)
			}
			for item in monthly_trends
		]
		
		return success_response(data={
			'trends': trends_data
		})


class ActivityAnalyticsByFacilityAPIView(APIView):
	"""Get detailed analytics broken down by facility."""
	permission_classes = [IsAuthenticated, HasCapability]
	required_capability = 'submit_activity'
	
	def get(self, request):
		org, membership = get_org_and_membership(request=request)
		
		# Get filters
		reporting_period_id = request.query_params.get('reporting_period_id')
		scope = request.query_params.get('scope')
		
		queryset = ActivitySubmission.objects.filter(
			organization=org,
			facility__isnull=False
		)
		
		if reporting_period_id:
			queryset = queryset.filter(reporting_period_id=reporting_period_id)
		if scope:
			queryset = queryset.filter(activity_type__scope__code=scope)
		
		# By facility
		facility_stats = queryset.values(
			'facility__id',
			'facility__name',
			'facility__location'
		).annotate(
			submission_count=Count('id'),
			total_value=Sum('value'),
			unique_activity_types=Count('activity_type', distinct=True)
		).order_by('-total_value')
		
		# For each facility, get breakdown by scope
		facility_data = []
		for facility_stat in facility_stats:
			facility_id = facility_stat['facility__id']
			
			# Get scope breakdown for this facility
			scope_breakdown = queryset.filter(
				facility_id=facility_id
			).values(
				'activity_type__scope__code',
				'activity_type__scope__name'
			).annotate(
				submission_count=Count('id'),
				total_value=Sum('value')
			).order_by('activity_type__scope__code')
			
			facility_data.append({
				'facility': {
					'id': str(facility_id),
					'name': facility_stat['facility__name'],
					'location': facility_stat['facility__location']
				},
				'totals': {
					'submission_count': facility_stat['submission_count'],
					'total_value': float(facility_stat['total_value'] or 0),
					'unique_activity_types': facility_stat['unique_activity_types']
				},
				'by_scope': [
					{
						'scope': item['activity_type__scope__code'],
						'scope_name': item['activity_type__scope__name'],
						'submission_count': item['submission_count'],
						'total_value': float(item['total_value'] or 0)
					}
					for item in scope_breakdown
				]
			})
		
		return success_response(data={'facilities': facility_data})


class ActivityAnalyticsComparisonAPIView(APIView):
	"""Compare activity submissions across reporting periods."""
	permission_classes = [IsAuthenticated, HasCapability]
	required_capability = 'submit_activity'
	
	def get(self, request):
		org, membership = get_org_and_membership(request=request)
		
		# Get filters
		activity_type_id = request.query_params.get('activity_type_id')
		scope = request.query_params.get('scope')
		
		queryset = ActivitySubmission.objects.filter(organization=org)
		
		if activity_type_id:
			queryset = queryset.filter(activity_type_id=activity_type_id)
		if scope:
			queryset = queryset.filter(activity_type__scope__code=scope)
		
		# Group by reporting period
		period_comparison = queryset.values(
			'reporting_period__id',
			'reporting_period__year',
			'reporting_period__quarter'
		).annotate(
			submission_count=Count('id'),
			total_value=Sum('value'),
			avg_value=Avg('value'),
			unique_activity_types=Count('activity_type', distinct=True)
		).order_by('reporting_period__year', 'reporting_period__quarter')
		
		return success_response(data={
			'comparison': [
				{
					'period': {
						'id': str(item['reporting_period__id']),
						'year': item['reporting_period__year'],
						'quarter': item['reporting_period__quarter']
					},
					'submission_count': item['submission_count'],
					'total_value': float(item['total_value'] or 0),
					'avg_value': float(item['avg_value'] or 0),
					'unique_activity_types': item['unique_activity_types']
				}
				for item in period_comparison
			]
		})
