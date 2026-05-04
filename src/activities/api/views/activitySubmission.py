from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.db import transaction

from common.api import success_response, problem_response
from accounts.selectors.org_context import get_org_and_membership
from ..serializers import ActivitySubmissionCreateSerializer, ActivitySubmissionSerializer
from submissions.services.activity import submit_activity_value
from django.conf import settings


def _submit_one(org, user, data):
	return submit_activity_value(
		org=org,
		user=user,
		activity_type_id=str(data['activity_type_id']),
		facility_id=str(data.get('facility_id')) if data.get('facility_id') else None,
		value=data['value'],
	)


class ActivitySubmissionCreateAPIView(APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request):
		org, _ = get_org_and_membership(request=request)

		# ---------------------------------------------------------------
		# Bulk path: body is a JSON array
		# ---------------------------------------------------------------
		if isinstance(request.data, list):
			if len(request.data) == 0:
				return problem_response({
					'type': f"{settings.PROBLEM_BASE_URL}/bad_request",
					'title': 'Invalid Request',
					'detail': 'Submissions array must not be empty',
				}, status.HTTP_400_BAD_REQUEST)

			if len(request.data) > 100:
				return problem_response({
					'type': f"{settings.PROBLEM_BASE_URL}/bad_request",
					'title': 'Invalid Request',
					'detail': 'Maximum 100 submissions per request',
				}, status.HTTP_400_BAD_REQUEST)

			created = []
			errors = []

			with transaction.atomic():
				for idx, item in enumerate(request.data):
					serializer = ActivitySubmissionCreateSerializer(data=item)
					if not serializer.is_valid():
						errors.append({'index': idx, 'errors': serializer.errors})
						continue
					try:
						obj = _submit_one(org, request.user, serializer.validated_data)
						created.append(obj)
					except ValidationError as e:
						errors.append({'index': idx, 'errors': e.detail if hasattr(e, 'detail') else str(e)})
					except PermissionDenied as e:
						errors.append({'index': idx, 'errors': e.detail if hasattr(e, 'detail') else str(e)})
					except Exception as e:
						errors.append({'index': idx, 'errors': str(e)})

			out = ActivitySubmissionSerializer(created, many=True)
			response_status = status.HTTP_201_CREATED if created else status.HTTP_400_BAD_REQUEST
			return success_response(data={
				'created': out.data,
				'created_count': len(created),
				'error_count': len(errors),
				'errors': errors,
			}, status=response_status)

		# ---------------------------------------------------------------
		# Single path: body is a JSON object (backward compatible)
		# ---------------------------------------------------------------
		serializer = ActivitySubmissionCreateSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		try:
			obj = _submit_one(org, request.user, serializer.validated_data)
		except ValidationError as e:
			return problem_response({
				'type': f"{settings.PROBLEM_BASE_URL}/bad_request",
				'title': 'Invalid Request',
				'detail': e.detail if hasattr(e, 'detail') else str(e),
			}, status.HTTP_400_BAD_REQUEST)
		except PermissionDenied as e:
			return problem_response({
				'type': f"{settings.PROBLEM_BASE_URL}/forbidden",
				'title': 'Forbidden',
				'detail': e.detail if hasattr(e, 'detail') else str(e),
			}, status.HTTP_403_FORBIDDEN)
		except Exception as e:
			return problem_response({
				'type': f"{settings.PROBLEM_BASE_URL}/server-error",
				'title': 'Server Error',
				'detail': str(e),
			}, status.HTTP_500_INTERNAL_SERVER_ERROR)

		out = ActivitySubmissionSerializer(obj)
		return success_response(data=out.data, status=status.HTTP_201_CREATED)
