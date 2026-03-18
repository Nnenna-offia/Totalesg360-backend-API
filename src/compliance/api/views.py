from rest_framework.views import APIView
from rest_framework import status
from django.conf import settings
from common.permissions import IsOrgMember, HasCapability
from common.api import success_response, problem_response

from compliance.services import compute_organization_compliance, compute_framework_completion, service_get_missing_indicators


class OrganizationComplianceView(APIView):
    permission_classes = [IsOrgMember, HasCapability]
    required_capability = 'compliance.view'

    def get(self, request):
        org = getattr(request, 'organization', None)
        period_id = request.query_params.get('period_id')
        if not org or not period_id:
            problem = {
                'type': 'f"{settings.PROBLEM_BASE_URL}/invalid-request',
                'title': 'Invalid request',
                'detail': 'organization and period_id required',
            }
            return problem_response(problem, status.HTTP_400_BAD_REQUEST)

        from submissions.models import ReportingPeriod
        period = ReportingPeriod.objects.filter(id=period_id).first()
        if not period:
            problem = {
                'type': f"{settings.PROBLEM_BASE_URL}/not-found",
                'title': 'Reporting period not found',
                'detail': 'reporting period not found',
            }
            return problem_response(problem, status.HTTP_404_NOT_FOUND)

        res = compute_organization_compliance(org, period)
        return success_response(res)


class FrameworkComplianceView(APIView):
    permission_classes = [IsOrgMember, HasCapability]
    required_capability = 'compliance.view'

    def get(self, request, framework_id):
        org = getattr(request, 'organization', None)
        period_id = request.query_params.get('period_id')
        if not org or not period_id:
            problem = {
                'type': f"{settings.PROBLEM_BASE_URL}/invalid-request",
                'title': 'Invalid request',
                'detail': 'organization and period_id required',
            }
            return problem_response(problem, status.HTTP_400_BAD_REQUEST)

        from organizations.models.regulatory_framework import RegulatoryFramework
        from submissions.models import ReportingPeriod

        framework = RegulatoryFramework.objects.filter(id=framework_id).first()
        if not framework:
            problem = {
                'type': f"{settings.PROBLEM_BASE_URL}/not-found",
                'title': 'Framework not found',
                'detail': 'framework not found',
            }
            return problem_response(problem, status.HTTP_404_NOT_FOUND)

        period = ReportingPeriod.objects.filter(id=period_id).first()
        if not period:
            problem = {
                'type': f"{settings.PROBLEM_BASE_URL}/not-found",
                'title': 'Reporting period not found',
                'detail': 'reporting period not found',
            }
            return problem_response(problem, status.HTTP_404_NOT_FOUND)

        res = compute_framework_completion(org, framework, period)
        return success_response(res)


class MissingIndicatorsView(APIView):
    permission_classes = [IsOrgMember, HasCapability]
    required_capability = 'compliance.view'

    def get(self, request):
        org = getattr(request, 'organization', None)
        framework_id = request.query_params.get('framework_id')
        period_id = request.query_params.get('period_id')
        if not org or not period_id or not framework_id:
            problem = {
                'type': f"{settings.PROBLEM_BASE_URL}/invalid-request",
                'title': 'Invalid request',
                'detail': 'organization, framework_id and period_id required',
            }
            return problem_response(problem, status.HTTP_400_BAD_REQUEST)

        from organizations.models.regulatory_framework import RegulatoryFramework
        from submissions.models import ReportingPeriod

        framework = RegulatoryFramework.objects.filter(id=framework_id).first()
        period = ReportingPeriod.objects.filter(id=period_id).first()
        if not framework or not period:
            problem = {
                'type': f"{settings.PROBLEM_BASE_URL}/not-found",
                'title': 'Framework or period not found',
                'detail': 'framework or period not found',
            }
            return problem_response(problem, status.HTTP_404_NOT_FOUND)

        missing = service_get_missing_indicators(org, framework, period)
        # Serialize minimal indicator info
        data = [{'id': getattr(i, 'id', None), 'code': getattr(i, 'code', None), 'name': getattr(i, 'name', None)} for i in missing]
        return success_response({'missing': data})
