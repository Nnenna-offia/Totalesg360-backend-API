from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from common.permissions import IsOrgMember, HasCapability
from common.api import success_response, problem_response
from dashboard.services.dashboard_service import get_dashboard_summary
from dashboard.models import DashboardMetric, IndicatorSnapshot, TargetSnapshot
from dashboard.selectors.dashboard_selectors import get_emissions_summary, get_social_metrics, get_governance_metrics


class DashboardSummaryView(APIView):
    permission_classes = [IsOrgMember, HasCapability]

    def get(self, request, *args, **kwargs):
        org = request.organization
        if not request.user:
            return Response(problem_response('authentication_required', 'Authentication required'), status=status.HTTP_401_UNAUTHORIZED)
        self.capability = 'dashboard.view'
        summary = get_dashboard_summary(org)
        return success_response(summary)


class DashboardEnvironmentalView(APIView):
    permission_classes = [IsOrgMember, HasCapability]

    def get(self, request, *args, **kwargs):
        org = request.organization
        self.capability = 'dashboard.view'
        metric = DashboardMetric.objects.filter(organization=org).order_by('-calculated_at').first()
        if metric:
            return success_response({'environmental_score': metric.environmental_score})
        # fallback
        env = get_emissions_summary(org)
        total_emissions = sum(env.values()) if isinstance(env, dict) else 0.0
        emissions_score = max(0, 100 - (total_emissions / 1000.0)) if total_emissions else 100
        return success_response({'environmental_score': emissions_score})


class DashboardSocialView(APIView):
    permission_classes = [IsOrgMember, HasCapability]

    def get(self, request, *args, **kwargs):
        org = request.organization
        self.capability = 'dashboard.view'
        metric = DashboardMetric.objects.filter(organization=org).order_by('-calculated_at').first()
        if metric:
            return success_response({'social_score': metric.social_score})
        soc = get_social_metrics(org)
        return success_response({'social_metrics': soc})


class DashboardGovernanceView(APIView):
    permission_classes = [IsOrgMember, HasCapability]

    def get(self, request, *args, **kwargs):
        org = request.organization
        self.capability = 'dashboard.view'
        metric = DashboardMetric.objects.filter(organization=org).order_by('-calculated_at').first()
        if metric:
            return success_response({'governance_score': metric.governance_score})
        gov = get_governance_metrics(org)
        return success_response({'governance_metrics': gov})


class DashboardTargetsView(APIView):
    permission_classes = [IsOrgMember, HasCapability]

    def get(self, request, *args, **kwargs):
        org = request.organization
        self.capability = 'dashboard.view'
        qs = TargetSnapshot.objects.filter(organization=org).order_by('-calculated_at')
        if qs.exists():
            items = [
                {
                    'target_id': str(t.target_id),
                    'current_value': t.current_value,
                    'progress_percent': t.progress_percent,
                    'status': t.status,
                }
                for t in qs
            ]
            return success_response({'targets': items})
        # fallback: empty list (or compute live if needed)
        return success_response({'targets': []})


class DashboardTrendsView(APIView):
    permission_classes = [IsOrgMember, HasCapability]

    def get(self, request, *args, **kwargs):
        org = request.organization
        self.capability = 'dashboard.view'
        # return recent indicator snapshots grouped by indicator
        qs = IndicatorSnapshot.objects.filter(organization=org).order_by('indicator_id', '-calculated_at')[:1000]
        grouped = {}
        for s in qs:
            grouped.setdefault(str(s.indicator_id), []).append({'value': s.value, 'calculated_at': s.calculated_at.isoformat(), 'unit': s.unit})
        return success_response({'trends': grouped})
