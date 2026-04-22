from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import transaction

from common.api import success_response, problem_response
from common.permissions import HasCapability
from accounts.selectors.org_context import get_org_and_membership
from submissions.services.activity import submit_activity_value
from ..serializers import ActivitySubmissionCreateSerializer, ActivitySubmissionListSerializer


class ActivitySubmissionBulkCreateAPIView(APIView):
	"""Bulk create multiple activity submissions in a single request."""
	permission_classes = [IsAuthenticated, HasCapability]
	required_capability = 'submit_activity'
	
	def post(self, request):
		"""
		Create multiple activity submissions.
		Payload: { "submissions": [...] }
		Each submission should have: activity_type_id, facility_id (optional), value
		"""
		org, membership = get_org_and_membership(request=request)
		
		submissions_data = request.data.get('submissions', [])
		
		if not submissions_data:
			return problem_response({
				'type': f"{settings.PROBLEM_BASE_URL}/bad_request",
				'title': 'Invalid Request',
				'detail': 'No submissions provided'
			}, status.HTTP_400_BAD_REQUEST)
		
		if len(submissions_data) > 100:
			return problem_response({
				'type': f"{settings.PROBLEM_BASE_URL}/bad_request",
				'title': 'Invalid Request',
				'detail': 'Maximum 100 submissions per bulk request'
			}, status.HTTP_400_BAD_REQUEST)
		
		created_submissions = []
		errors = []
		
		with transaction.atomic():
			for idx, submission_data in enumerate(submissions_data):
				serializer = ActivitySubmissionCreateSerializer(data=submission_data)
				
				if not serializer.is_valid():
					errors.append({
						'index': idx,
						'data': submission_data,
						'errors': serializer.errors
					})
					continue
				
				try:
					data = serializer.validated_data
					obj = submit_activity_value(
						org=org,
						user=request.user,
						activity_type_id=str(data['activity_type_id']),
						facility_id=str(data.get('facility_id')) if data.get('facility_id') else None,
						value=data['value'],
					)
					created_submissions.append(obj)
				except Exception as e:
					errors.append({
						'index': idx,
						'data': submission_data,
						'errors': {'non_field_errors': [str(e)]}
					})
		
		# Serialize created submissions
		out_serializer = ActivitySubmissionListSerializer(created_submissions, many=True)
		
		return success_response(data={
			'created': out_serializer.data,
			'created_count': len(created_submissions),
			'error_count': len(errors),
			'errors': errors
		}, status=status.HTTP_201_CREATED if created_submissions else status.HTTP_400_BAD_REQUEST)


class ActivitySubmissionBulkDeleteAPIView(APIView):
	"""Bulk delete multiple activity submissions."""
	permission_classes = [IsAuthenticated, HasCapability]
	required_capability = 'submit_activity'
	
	def post(self, request):
		"""
		Delete multiple activity submissions.
		Payload: { "submission_ids": ["uuid1", "uuid2", ...] }
		"""
		org, membership = get_org_and_membership(request=request)
		
		submission_ids = request.data.get('submission_ids', [])
		
		if not submission_ids:
			return problem_response(
				message="No submission IDs provided",
				status=status.HTTP_400_BAD_REQUEST
			)
		
		if len(submission_ids) > 100:
			return problem_response(
				message="Maximum 100 submissions per bulk delete",
				status=status.HTTP_400_BAD_REQUEST
			)
		
		from submissions.models.activity_submission import ActivitySubmission
		
		# Get submissions
		submissions = ActivitySubmission.objects.filter(
			id__in=submission_ids,
			organization=org
		).select_related('reporting_period', 'activity_type')
		
		# Check for locked periods
		locked_submissions = []
		deletable_submissions = []
		
		for submission in submissions:
			if submission.reporting_period.status not in ['draft', 'open']:
				locked_submissions.append({
					'id': str(submission.id),
					'reason': f"Period is {submission.reporting_period.status}"
				})
			else:
				deletable_submissions.append(submission)
		
		deleted_count = 0
		with transaction.atomic():
			for submission in deletable_submissions:
				# Store info for recalculation
				activity_type = submission.activity_type
				reporting_period = submission.reporting_period
				facility = submission.facility
				
				submission.delete()
				deleted_count += 1
				
				# Trigger recalculation
				if activity_type.indicator:
					from indicators.services.indicator_aggregation import update_indicator_value
					from types import SimpleNamespace
					try:
						mock_submission = SimpleNamespace(
							organization=org,
							activity_type=activity_type,
							reporting_period=reporting_period,
							facility=facility
						)
						update_indicator_value(activity_submission=mock_submission)
					except Exception:
						pass
		
		return success_response(data={
			'deleted_count': deleted_count,
			'requested_count': len(submission_ids),
			'locked_count': len(locked_submissions),
			'locked_submissions': locked_submissions
		})
