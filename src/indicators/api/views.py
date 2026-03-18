from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.pagination import PageNumberPagination
from common.permissions import HasGlobalCapability

from indicators.models import Indicator
from .serializers import IndicatorSerializer


class IndicatorViewSet(viewsets.ModelViewSet):
	"""Admin-managed CRUD for global Indicators.

	Read (GET) is public; writes require admin.
	"""
	queryset = Indicator.objects.all().order_by('code')
	serializer_class = IndicatorSerializer
	pagination_class = PageNumberPagination
	required_capability = 'indicator.manage'

	def get_permissions(self):
		# allow anyone to list/retrieve
		if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
			return [AllowAny()]
		# allow staff or global capability holders
		return [HasGlobalCapability()]


from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from common.api import success_response
from accounts.selectors.org_context import get_org_and_membership
from submissions.models import ReportingPeriod
from indicators.selectors.queries import get_indicator_emission_value


class EmissionIndicatorValueAPIView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request, code):
		org, _ = get_org_and_membership(request=request)
		period_id = request.query_params.get('reporting_period_id')
		if not org or not period_id:
			return success_response(data={'detail': 'organization and reporting_period_id required'}, status=400)
		try:
			period = ReportingPeriod.objects.get(id=period_id, organization=org)
		except ReportingPeriod.DoesNotExist:
			return success_response(data={'detail': 'reporting_period not found'}, status=404)

		val = get_indicator_emission_value(code, org=org, reporting_period=period)
		return success_response(data={'indicator_code': code, 'value': val})
