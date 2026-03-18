from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from common.api import success_response
from accounts.selectors.org_context import get_org_and_membership
from submissions.models import ReportingPeriod
from emissions.selectors.queries import (
	get_scope1_emissions,
	get_scope2_emissions,
	get_scope3_emissions,
	get_total_emissions,
)


class ScopeEmissionsAPIView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request, scope):
		org, _ = get_org_and_membership(request=request)
		period_id = request.query_params.get('reporting_period_id')
		if not period_id:
			return success_response(data={'detail': 'reporting_period_id required'}, status=400)
		period = ReportingPeriod.objects.get(id=period_id, organization=org)

		if scope == 'scope1':
			total = get_scope1_emissions(org, period)
		elif scope == 'scope2':
			total = get_scope2_emissions(org, period)
		elif scope == 'scope3':
			total = get_scope3_emissions(org, period)
		elif scope == 'total':
			total = get_total_emissions(org, period)
		else:
			return success_response(data={'detail': 'invalid scope'}, status=400)

		return success_response(data={'scope': scope, 'total': total})

