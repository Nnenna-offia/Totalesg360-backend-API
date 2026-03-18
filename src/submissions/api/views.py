from rest_framework.views import APIView
from rest_framework import status, parsers
from rest_framework.exceptions import ParseError as DRFParseError

from common.permissions import IsOrgMember, HasCapability
from common.api import success_response, problem_response
from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
import logging
from accounts.selectors.org_context import get_org_and_membership
from submissions.api.serializers import SubmissionCreateSerializer, DataSubmissionSerializer
from submissions.services import submit_indicator_value, finalize_period, approve_submission
from submissions.selectors.queries import get_period_submissions
from submissions.services.core import fetch_period_submissions
from rest_framework.pagination import PageNumberPagination
from submissions.models import ReportingPeriod
from submissions.api.serializers import ReportingPeriodSerializer
from rest_framework.permissions import IsAdminUser


class SubmitIndicatorAPIView(APIView):
	permission_classes = [IsOrgMember, HasCapability]
	required_capability = "indicator.manage"

	def post(self, request):
		org, membership = get_org_and_membership(request=request)
		serializer = SubmissionCreateSerializer(data=request.data, context={"org": org})
		serializer.is_valid(raise_exception=True)
		data = serializer.validated_data

		try:
			obj, created = submit_indicator_value(
				org=org,
				user=request.user,
				indicator_id=str(data["indicator_id"]),
				reporting_period_id=str(data["reporting_period_id"]),
				facility_id=str(data.get("facility_id")) if data.get("facility_id") else None,
				value=data.get("value"),
				metadata=data.get("metadata"),
			)
		except DjangoValidationError as exc:
			return problem_response({'type': f"{settings.PROBLEM_BASE_URL}/invalid-request", 'title': 'Invalid payload', 'detail': str(exc)}, status.HTTP_400_BAD_REQUEST)
		except PermissionDenied as exc:
			return problem_response({'type': f"{settings.PROBLEM_BASE_URL}/forbidden", 'title': 'Forbidden', 'detail': str(exc)}, status.HTTP_403_FORBIDDEN)
		except Exception:
			logging.exception('Unexpected error in submit_indicator_value for org %s', getattr(org, 'id', None))
			return problem_response({'type': f"{settings.PROBLEM_BASE_URL}/internal-server-error", 'title': 'Internal Server Error', 'detail': 'An unexpected error occurred.'}, status.HTTP_500_INTERNAL_SERVER_ERROR)

		out = DataSubmissionSerializer(obj)
		return success_response(data=out.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class PeriodSubmissionsAPIView(APIView):
	permission_classes = [IsOrgMember]

	def get(self, request, period_id):
		org, _ = get_org_and_membership(request=request)
		# read filters from query params
		pillar = request.query_params.get("pillar")
		indicator_code = request.query_params.get("indicator_code")
		submission_status = request.query_params.get("status")
		facility_id = request.query_params.get("facility_id")

		try:
			results = fetch_period_submissions(
				org=org,
				reporting_period_id=str(period_id),
				pillar=pillar,
				indicator_code=indicator_code,
				submission_status=submission_status,
				facility_id=facility_id,
			)
		except Exception as exc:
			from django.core.exceptions import ValidationError as DjangoValidationError
			if isinstance(exc, DjangoValidationError):
				problem = {
					"type": f"{settings.PROBLEM_BASE_URL}/not-found",
					"title": "Not found",
					"status": status.HTTP_404_NOT_FOUND,
					"detail": str(exc),
					"instance": getattr(request, "path", None),
				}
				return problem_response(problem, status.HTTP_404_NOT_FOUND)
				raise

		# Paginate the results list
		paginator = PageNumberPagination()
		# allow client to set page_size via `page_size` query param if desired
		paginator.page_size_query_param = 'page_size'
		page = paginator.paginate_queryset(results, request, view=self)

		from .serializers import IndicatorSummarySerializer
		# If paginator did not paginate (page is None), return full results with simple meta
		if page is None:
			out = IndicatorSummarySerializer(results, many=True)
			meta = {
				"count": len(results),
				"page_size": None,
				"current_page": None,
				"next": None,
				"previous": None,
			}
			return success_response(data=out.data, meta=meta)

		out = IndicatorSummarySerializer(page, many=True)

		# build meta from paginator
		meta = {
			"count": paginator.page.paginator.count if getattr(paginator, 'page', None) is not None else len(results),
			"page_size": paginator.get_page_size(request) or None,
			"current_page": getattr(paginator.page, 'number', None) if getattr(paginator, 'page', None) is not None else None,
			"next": paginator.get_next_link(),
			"previous": paginator.get_previous_link(),
		}

		return success_response(data=out.data, meta=meta)


class ReportingPeriodListCreateAPIView(APIView):
	"""List and create reporting periods for the resolved org.

	GET: list periods for org
	POST: create reporting period (requires `manage_period` capability)
	"""
	permission_classes = [IsOrgMember]

	def get(self, request):
		org, _ = get_org_and_membership(request=request)
		qs = ReportingPeriod.objects.filter(organization=org).order_by('-year', '-quarter')

		# Paginate reporting periods
		from rest_framework.pagination import PageNumberPagination
		paginator = PageNumberPagination()
		paginator.page_size_query_param = 'page_size'
		page = paginator.paginate_queryset(qs, request, view=self)

		# If paginator didn't paginate (page is None), return full queryset
		if page is None:
			serializer = ReportingPeriodSerializer(qs, many=True)
			meta = {
				"count": qs.count(),
				"page_size": None,
				"current_page": None,
				"next": None,
				"previous": None,
			}
			return success_response(data=serializer.data, meta=meta)

		serializer = ReportingPeriodSerializer(page, many=True)

		meta = {
			"count": paginator.page.paginator.count if getattr(paginator, 'page', None) is not None else qs.count(),
			"page_size": paginator.get_page_size(request) or None,
			"current_page": getattr(paginator.page, 'number', None) if getattr(paginator, 'page', None) is not None else None,
			"next": paginator.get_next_link(),
			"previous": paginator.get_previous_link(),
		}

		return success_response(data=serializer.data, meta=meta)

	# creation restricted to users with manage_period capability
	required_capability = 'manage_period'

	def get_permissions(self):
		# GET: only require org membership
		if self.request.method == 'GET':
			return [IsOrgMember()]
		# POST and other write methods require manage_period capability
		return [IsOrgMember(), HasCapability()]

	def post(self, request):
		org, _ = get_org_and_membership(request=request)
		serializer = ReportingPeriodSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		rp = serializer.save(organization=org)
		out = ReportingPeriodSerializer(rp)
		return success_response(data=out.data, status=status.HTTP_201_CREATED)


class FinalizePeriodAPIView(APIView):
	permission_classes = [IsOrgMember, HasCapability]
	required_capability = "manage_period"

	def post(self, request, period_id):
		org, _ = get_org_and_membership(request=request)
		try:
			finalize_period(org=org, user=request.user, reporting_period_id=str(period_id))
		except Exception as exc:
			# convert Django ValidationError -> problem_response (400), let other exceptions bubble
			from django.core.exceptions import ValidationError as DjangoValidationError
			if isinstance(exc, DjangoValidationError):
				problem = {
					"type": f"{settings.PROBLEM_BASE_URL}/validation-error",
					"title": "Validation error",
					"status": status.HTTP_400_BAD_REQUEST,
					"detail": str(exc),
					"instance": getattr(request, "path", None),
				}
				return problem_response(problem, status.HTTP_400_BAD_REQUEST)
			raise

		return success_response(data={"detail": "Period finalized"})


class ApproveSubmissionAPIView(APIView):
	permission_classes = [IsOrgMember, HasCapability]
	# accept JSON or form/multipart; handle JSON parse errors explicitly
	parser_classes = [parsers.JSONParser, parsers.FormParser, parsers.MultiPartParser]
	required_capability = "approve_submission"

	def post(self, request, submission_id):
		org, _ = get_org_and_membership(request=request)
		try:
			sub = approve_submission(org=org, user=request.user, submission_id=str(submission_id))
		except DRFParseError as exc:
			problem = {
				"type": f"{settings.PROBLEM_BASE_URL}/invalid-request",
				"title": "Invalid request",
				"status": status.HTTP_400_BAD_REQUEST,
				"detail": str(exc),
				"instance": getattr(request, "path", None),
			}
			return problem_response(problem, status.HTTP_400_BAD_REQUEST)

		except DjangoValidationError as exc:
			problem = {
				"type": f"{settings.PROBLEM_BASE_URL}/not-found",
				"title": "Not found",
				"status": status.HTTP_404_NOT_FOUND,
				"detail": str(exc),
				"instance": getattr(request, "path", None),
			}
			return problem_response(problem, status.HTTP_404_NOT_FOUND)
		except PermissionDenied as exc:
			problem = {
				"type": f"{settings.PROBLEM_BASE_URL}/forbidden",
				"title": "Permission denied",
				"status": status.HTTP_403_FORBIDDEN,
				"detail": str(exc),
				"instance": getattr(request, "path", None),
			}
			return problem_response(problem, status.HTTP_403_FORBIDDEN)
		except Exception:
			logging.exception('Unexpected error approving submission %s for org %s', submission_id, getattr(org, 'id', None))
			problem = {
				"type": f"{settings.PROBLEM_BASE_URL}/internal-server-error",
				"title": "Internal Server Error",
				"status": status.HTTP_500_INTERNAL_SERVER_ERROR,
				"detail": "An unexpected error occurred.",
				"instance": getattr(request, "path", None),
			}
			return problem_response(problem, status.HTTP_500_INTERNAL_SERVER_ERROR)

		out = DataSubmissionSerializer(sub)
		return success_response(data=out.data)

