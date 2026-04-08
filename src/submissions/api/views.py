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
from submissions.api.serializers import ReportingPeriodSerializer, ReportingPeriodGenerationSerializer
from submissions.services.period_generation import generate_reporting_periods
from rest_framework.permissions import IsAdminUser
from submissions.api.serializers import ActiveReportingPeriodSerializer
from submissions.services.reporting_period import get_or_raise_active_reporting_period
from targets.models import TargetGoal


class SubmitIndicatorAPIView(APIView):
	permission_classes = [IsOrgMember, HasCapability]
	required_capability = "submit_indicator"

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
		qs = ReportingPeriod.objects.filter(organization=org).order_by('-start_date', 'name')

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
		"""
		Auto-generate reporting periods for a year.
		
		Accepts:
		{
		  "year": 2025,
		  "period_type": "QUARTERLY"
		}
		
		Generates all periods for that year (e.g., Q1-Q4 for QUARTERLY).
		Prevents duplicates - if periods already exist, returns existing ones.
		"""
		org, _ = get_org_and_membership(request=request)
		serializer = ReportingPeriodGenerationSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		
		year = serializer.validated_data['year']
		period_type = serializer.validated_data['period_type']
		
		# If a specific quarter was requested, create only that quarter
		req_quarter = serializer.validated_data.get('quarter') if hasattr(serializer, 'validated_data') else None
		if req_quarter:
			# compute quarter start/end
			from datetime import date
			q = int(req_quarter)
			if q not in (1, 2, 3, 4):
				raise Exception("Quarter must be 1-4")
			if q == 1:
				start = date(year, 1, 1)
				end = date(year, 3, 31)
			elif q == 2:
				start = date(year, 4, 1)
				end = date(year, 6, 30)
			elif q == 3:
				start = date(year, 7, 1)
				end = date(year, 9, 30)
			else:
				start = date(year, 10, 1)
				end = date(year, 12, 31)

			# Check if already exists
			existing_periods = ReportingPeriod.objects.filter(
				organization=org,
				period_type=ReportingPeriod.PeriodType.QUARTERLY,
				start_date=start,
				end_date=end,
			)
			if existing_periods.exists():
				out = ReportingPeriodSerializer(existing_periods.first())
				return success_response(data=out.data, meta={"message": "period exists", "created": False}, status=status.HTTP_200_OK)

			# create the period
			period = ReportingPeriod.objects.create(
				organization=org,
				name=f"Q{q} {year}",
				period_type=ReportingPeriod.PeriodType.QUARTERLY,
				start_date=start,
				end_date=end,
				status=ReportingPeriod.Status.OPEN,
				is_active=True,
				year=year,
				quarter=q,
			)
			out = ReportingPeriodSerializer(period)
			return success_response(data=out.data, meta={"created": True}, status=status.HTTP_201_CREATED)

		# Check if periods already exist for this org, year, and type
		existing_periods = ReportingPeriod.objects.filter(
			organization=org,
			period_type=period_type,
			start_date__year=year
		)
		
		if existing_periods.exists():
			# Return existing periods
			out = ReportingPeriodSerializer(existing_periods, many=True)
			return success_response(
				data=out.data,
				meta={
					"message": f"{period_type} periods for {year} already exist",
					"count": existing_periods.count(),
					"created": False
				},
				status=status.HTTP_200_OK
			)
		
		# Generate new periods
		try:
			results = generate_reporting_periods(
				organization=org,
				year=year,
				period_types=[period_type],
				save=True
			)
			
			generated_periods = results.get(period_type, [])
			
			if not generated_periods:
				return problem_response(
					{
						"type": f"{settings.PROBLEM_BASE_URL}/generation-failed",
						"title": "Period generation failed",
						"status": status.HTTP_500_INTERNAL_SERVER_ERROR,
						"detail": f"Failed to generate {period_type} periods for {year}",
						"instance": getattr(request, "path", None),
					},
					status.HTTP_500_INTERNAL_SERVER_ERROR
				)
			
			# Fetch the created periods from database to get complete data
			created_periods = ReportingPeriod.objects.filter(
				organization=org,
				period_type=period_type,
				start_date__year=year
			)
		
			# If only a single period was generated, return the object; else return list
			if created_periods.count() == 1:
				out = ReportingPeriodSerializer(created_periods.first())
				data_payload = out.data
			else:
				out = ReportingPeriodSerializer(created_periods, many=True)
				data_payload = out.data
		
			return success_response(
				data=data_payload,
				meta={
					"message": f"Successfully generated {len(generated_periods)} {period_type} periods for {year}",
					"count": len(generated_periods),
					"created": True
				},
				status=status.HTTP_201_CREATED
			)
			
		except Exception as exc:
			from django.core.exceptions import ValidationError as DjangoValidationError
			from django.db import IntegrityError
			
			if isinstance(exc, (DjangoValidationError, IntegrityError)):
				detail = str(exc)
				problem = {
					"type": f"{settings.PROBLEM_BASE_URL}/generation-error",
					"title": "Period generation error",
					"status": status.HTTP_400_BAD_REQUEST,
					"detail": detail,
					"instance": getattr(request, "path", None),
				}
				return problem_response(problem, status.HTTP_400_BAD_REQUEST)
			raise


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



class ActiveReportingPeriodAPIView(APIView):
    permission_classes = [IsOrgMember]

    def get(self, request):
        org, _ = get_org_and_membership(request=request)
        target_id = request.query_params.get('target_id')
        if not target_id:
            return problem_response({'type': f"{settings.PROBLEM_BASE_URL}/invalid-request", 'title': 'Invalid request', 'detail': 'target_id query parameter required'}, status.HTTP_400_BAD_REQUEST)

        try:
            target = TargetGoal.objects.get(id=target_id, organization=org)
        except TargetGoal.DoesNotExist:
            return problem_response({'type': f"{settings.PROBLEM_BASE_URL}/not-found", 'title': 'Not found', 'detail': 'Target not found'}, status.HTTP_404_NOT_FOUND)

        try:
            period = get_or_raise_active_reporting_period(org, target)
        except Exception as exc:
            return problem_response({'type': f"{settings.PROBLEM_BASE_URL}/not-found", 'title': 'Not found', 'detail': str(exc)}, status.HTTP_404_NOT_FOUND)

        # Build response matching expected schema
        data = {
            'id': str(period.id),
            'target_id': str(target.id),
            'name': period.name,
            'frequency': period.period_type,
            'status': period.status,
            'start_date': period.start_date,
            'end_date': period.end_date,
        }

        serializer = ActiveReportingPeriodSerializer(data)
        return success_response(data=serializer.data)

