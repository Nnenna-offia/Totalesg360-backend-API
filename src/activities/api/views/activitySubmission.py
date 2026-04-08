from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from common.api import success_response, problem_response
from accounts.selectors.org_context import get_org_and_membership
from ..serializers import ActivitySubmissionCreateSerializer, ActivitySubmissionSerializer
from submissions.services.activity import submit_activity_value
from django.conf import settings


class ActivitySubmissionCreateAPIView(APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request):
		org, membership = get_org_and_membership(request=request)
		serializer = ActivitySubmissionCreateSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		data = serializer.validated_data

		try:
			obj = submit_activity_value(
				org=org,
				user=request.user,
				activity_type_id=str(data['activity_type_id']),
				reporting_period_id=str(data['reporting_period_id']),
				facility_id=str(data.get('facility_id')) if data.get('facility_id') else None,
				value=data['value'],
			)
		except Exception as e:
			# Map DRF exceptions to problem responses
			from rest_framework.exceptions import ValidationError, PermissionDenied
			if isinstance(e, ValidationError):
				return problem_response({
					'type': f"{settings.PROBLEM_BASE_URL}/bad_request",
					'title': 'Invalid Request',
					'detail': e.detail if hasattr(e, 'detail') else str(e)
				}, status.HTTP_400_BAD_REQUEST)
			if isinstance(e, PermissionDenied):
				return problem_response({
					'type': f"{settings.PROBLEM_BASE_URL}/forbidden",
					'title': 'Forbidden',
					'detail': e.detail if hasattr(e, 'detail') else str(e)
				}, status.HTTP_403_FORBIDDEN)
			# Fallback
			return problem_response({
				'type': f"{settings.PROBLEM_BASE_URL}/server-error",
				'title': 'Server Error',
				'detail': str(e)
			}, status.HTTP_500_INTERNAL_SERVER_ERROR)

		out = ActivitySubmissionSerializer(obj)
		return success_response(data=out.data, status=status.HTTP_201_CREATED)
