from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from common.api import success_response, problem_response
from common.permissions import HasCapability
from accounts.selectors.org_context import get_org_and_membership
from submissions.models.activity_submission import ActivitySubmission
from submissions.models.reporting_period import ReportingPeriod
from ..serializers import ActivitySubmissionListSerializer, ActivitySubmissionUpdateSerializer


class ActivitySubmissionListAPIView(APIView):
	permission_classes = [IsAuthenticated, HasCapability]
	required_capability = 'submit_activity'
	
	def get(self, request):
		"""
		List activity submissions for the organization.
		Query params:
		- reporting_period_id: Filter by reporting period
		- activity_type_id: Filter by activity type
		- facility_id: Filter by facility
		- created_by_id: Filter by creator
		- scope: Filter by scope code
		"""
		org, membership = get_org_and_membership(request=request)
		
		queryset = ActivitySubmission.objects.filter(organization=org).select_related(
			'activity_type', 'activity_type__scope', 'facility', 
			'reporting_period', 'created_by'
		)
		
		# Filters
		reporting_period_id = request.query_params.get('reporting_period_id')
		if reporting_period_id:
			queryset = queryset.filter(reporting_period_id=reporting_period_id)
		
		activity_type_id = request.query_params.get('activity_type_id')
		if activity_type_id:
			queryset = queryset.filter(activity_type_id=activity_type_id)
		
		facility_id = request.query_params.get('facility_id')
		if facility_id:
			queryset = queryset.filter(facility_id=facility_id)
		
		created_by_id = request.query_params.get('created_by_id')
		if created_by_id:
			queryset = queryset.filter(created_by_id=created_by_id)
		
		scope = request.query_params.get('scope')
		if scope:
			queryset = queryset.filter(activity_type__scope__code=scope)
		
		queryset = queryset.order_by('-created_at')
		serializer = ActivitySubmissionListSerializer(queryset, many=True)
		return success_response(data=serializer.data)


class ActivitySubmissionDetailAPIView(APIView):
	permission_classes = [IsAuthenticated, HasCapability]
	required_capability = 'submit_activity'
	
	def get_object(self, org, pk):
		try:
			return ActivitySubmission.objects.select_related(
				'activity_type', 'activity_type__scope', 'facility', 
				'reporting_period', 'created_by'
			).get(pk=pk, organization=org)
		except ActivitySubmission.DoesNotExist:
			return None
	
	def get(self, request, pk):
		"""Get activity submission details."""
		org, membership = get_org_and_membership(request=request)
		
		submission = self.get_object(org, pk)
		if not submission:
			return problem_response(
				message="Activity submission not found",
				status=status.HTTP_404_NOT_FOUND
			)
		
		serializer = ActivitySubmissionListSerializer(submission)
		return success_response(data=serializer.data)
	
	def patch(self, request, pk):
		"""
		Update activity submission.
		Only value and unit can be updated.
		Triggers indicator recalculation.
		"""
		org, membership = get_org_and_membership(request=request)
		
		submission = self.get_object(org, pk)
		if not submission:
			return problem_response(
				message="Activity submission not found",
				status=status.HTTP_404_NOT_FOUND
			)
		
		# Check if reporting period is still open
		if submission.reporting_period.status not in ['draft', 'open']:
			return problem_response(
				message=f"Cannot update submission for {submission.reporting_period.status} period",
				status=status.HTTP_400_BAD_REQUEST
			)
		
		serializer = ActivitySubmissionUpdateSerializer(
			submission, 
			data=request.data, 
			partial=True
		)
		serializer.is_valid(raise_exception=True)
		submission = serializer.save()
		
		# Recalculate indicator value
		if submission.activity_type.indicator:
			from indicators.services.indicator_aggregation import update_indicator_value
			try:
				update_indicator_value(activity_submission=submission)
			except Exception as e:
				# Log but don't fail the update
				pass
		
		out_serializer = ActivitySubmissionListSerializer(submission)
		return success_response(data=out_serializer.data)
	
	def delete(self, request, pk):
		"""
		Delete activity submission.
		Triggers indicator recalculation.
		"""
		org, membership = get_org_and_membership(request=request)
		
		submission = self.get_object(org, pk)
		if not submission:
			return problem_response(
				message="Activity submission not found",
				status=status.HTTP_404_NOT_FOUND
			)
		
		# Check if reporting period is still open
		if submission.reporting_period.status not in ['draft', 'open']:
			return problem_response(
				message=f"Cannot delete submission for {submission.reporting_period.status} period",
				status=status.HTTP_400_BAD_REQUEST
			)
		
		# Store info for recalculation
		activity_type = submission.activity_type
		reporting_period = submission.reporting_period
		facility = submission.facility
		
		submission.delete()
		
		# Recalculate indicator value
		if activity_type.indicator:
			from indicators.services.indicator_aggregation import update_indicator_value
			try:
				# Create a mock object for recalculation
				from types import SimpleNamespace
				mock_submission = SimpleNamespace(
					organization=org,
					activity_type=activity_type,
					reporting_period=reporting_period,
					facility=facility
				)
				update_indicator_value(activity_submission=mock_submission)
			except Exception as e:
				# Log but don't fail the delete
				pass
		
		return success_response(
			message="Activity submission deleted successfully",
			status=status.HTTP_204_NO_CONTENT
		)


class ActivitySubmissionsByPeriodAPIView(APIView):
	"""Get all activity submissions for a specific reporting period with aggregations."""
	permission_classes = [IsAuthenticated, HasCapability]
	required_capability = 'submit_activity'
	
	def get(self, request, period_id):
		org, membership = get_org_and_membership(request=request)
		
		# Verify period exists and belongs to org
		try:
			period = ReportingPeriod.objects.get(pk=period_id, organization=org)
		except ReportingPeriod.DoesNotExist:
			return problem_response(
				message="Reporting period not found",
				status=status.HTTP_404_NOT_FOUND
			)
		
		# Get submissions
		queryset = ActivitySubmission.objects.filter(
			organization=org,
			reporting_period=period
		).select_related(
			'activity_type', 'activity_type__scope', 'facility', 'created_by'
		).order_by('activity_type__scope__code', 'activity_type__name', 'created_at')
		
		# Apply filters
		activity_type_id = request.query_params.get('activity_type_id')
		if activity_type_id:
			queryset = queryset.filter(activity_type_id=activity_type_id)
		
		facility_id = request.query_params.get('facility_id')
		if facility_id:
			queryset = queryset.filter(facility_id=facility_id)
		
		scope = request.query_params.get('scope')
		if scope:
			queryset = queryset.filter(activity_type__scope__code=scope)
		
		# Serialize
		serializer = ActivitySubmissionListSerializer(queryset, many=True)
		
		# Calculate aggregations
		from django.db.models import Count, Sum
		aggregations = queryset.aggregate(
			total_count=Count('id'),
			total_value=Sum('value')
		)
		
		# Group by scope
		scope_summary = {}
		for submission in queryset:
			scope_code = submission.activity_type.scope.code if submission.activity_type.scope else 'unknown'
			if scope_code not in scope_summary:
				scope_summary[scope_code] = {
					'scope': scope_code,
					'count': 0,
					'total_value': 0
				}
			scope_summary[scope_code]['count'] += 1
			scope_summary[scope_code]['total_value'] += float(submission.value)
		
		return success_response(data={
			'period': {
				'id': str(period.id),
				'year': period.year,
				'quarter': period.quarter,
				'status': period.status
			},
			'summary': {
				'total_submissions': aggregations['total_count'],
				'total_value': float(aggregations['total_value'] or 0),
				'by_scope': list(scope_summary.values())
			},
			'submissions': serializer.data
		})
