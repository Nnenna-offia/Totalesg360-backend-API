"""API views for Group Analytics."""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.conf import settings

from common.api import success_response, problem_response
from common.permissions import IsOrgMember
from organizations.models import Organization
from submissions.models import ReportingPeriod
from group_analytics.selectors import (
    get_group_dashboard,
    get_group_framework_readiness,
    get_subsidiary_ranking,
    get_group_top_gaps,
    get_group_recommendations,
    calculate_group_esg_score,
    get_group_portfolio_summary,
    get_subsidiary_comparison,
)
from .serializers import (
    GroupDashboardSerializer,
    GroupReadinessResponseSerializer,
    SubsidiaryRankingSerializer,
    ComplianceGapSerializer,
    ComplianceRecommendationSerializer,
    ESGScoreSerializer,
    PortfolioSummarySerializer,
    SubsidiaryComparisonSerializer,
)


class GroupDashboardView(APIView):
    """
    Get comprehensive group dashboard.
    
    GET /api/v1/group/dashboard/
    """
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def get(self, request):
        org = getattr(request, 'organization', None)
        
        if not org:
            problem = {
                'type': f"{settings.PROBLEM_BASE_URL}/organization-not-found",
                'title': 'Organization not found',
                'detail': 'Organization not found',
            }
            return problem_response(problem, status.HTTP_400_BAD_REQUEST)
        
        # Verify user is accessing their own organization
        if str(org.id) != request.query_params.get('organization_id', str(org.id)):
            problem = {
                'type': f"{settings.PROBLEM_BASE_URL}/unauthorized",
                'title': 'Unauthorized',
                'detail': 'Unauthorized access',
            }
            return problem_response(problem, status.HTTP_403_FORBIDDEN)
        
        # Check if this is a group/parent organization
        if org.organization_type not in ['group']:
            problem = {
                'type': f"{settings.PROBLEM_BASE_URL}/invalid-organization-type",
                'title': 'Invalid organization type',
                'detail': 'This endpoint is only available for group organizations',
            }
            return problem_response(problem, status.HTTP_400_BAD_REQUEST)
        
        try:
            dashboard = get_group_dashboard(org)
            serializer = GroupDashboardSerializer(dashboard)
            
            return success_response(
                data=serializer.data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            problem = {
                'type': f"{settings.PROBLEM_BASE_URL}/server-error",
                'title': 'Server error',
                'detail': f"Error fetching dashboard: {str(e)}",
            }
            return problem_response(problem, status.HTTP_500_INTERNAL_SERVER_ERROR)


class GroupFrameworkReadinessView(APIView):
    """
    Get group framework readiness aggregation.
    
    GET /api/v1/group/framework-readiness/
    """
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def get(self, request):
        org = getattr(request, 'organization', None)
        
        if not org or org.organization_type not in ['group']:
            problem = {
                'type': f"{settings.PROBLEM_BASE_URL}/group-not-found",
                'title': 'Group organization not found',
                'detail': 'Group organization not found',
            }
            return problem_response(problem, status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get reporting period
            period_id = request.query_params.get('reporting_period_id')
            reporting_period = None
            
            if period_id:
                reporting_period = ReportingPeriod.objects.filter(id=period_id).first()
            else:
                reporting_period = ReportingPeriod.objects.filter(
                    organization=org
                ).order_by('-end_date').first()
            
            if not reporting_period:
                problem = {
                    'type': f"{settings.PROBLEM_BASE_URL}/not-found",
                    'title': 'Reporting period not found',
                    'detail': 'No reporting period found',
                }
                return problem_response(problem, status.HTTP_404_NOT_FOUND)
            
            readiness = get_group_framework_readiness(org, reporting_period)
            serializer = GroupReadinessResponseSerializer(readiness)
            
            return success_response(
                data=serializer.data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            problem = {
                'type': f"{settings.PROBLEM_BASE_URL}/server-error",
                'title': 'Server error',
                'detail': f"Error fetching framework readiness: {str(e)}",
            }
            return problem_response(problem, status.HTTP_500_INTERNAL_SERVER_ERROR)


class GroupESGScoreView(APIView):
    """
    Get group ESG score.
    
    GET /api/v1/group/esg-score/
    """
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def get(self, request):
        org = getattr(request, 'organization', None)
        
        if not org or org.organization_type not in ['group']:
            problem = {
                'type': f"{settings.PROBLEM_BASE_URL}/group-not-found",
                'title': 'Group organization not found',
                'detail': 'Group organization not found',
            }
            return problem_response(problem, status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get reporting period
            period_id = request.query_params.get('reporting_period_id')
            reporting_period = None
            
            if period_id:
                reporting_period = ReportingPeriod.objects.filter(id=period_id).first()
            else:
                reporting_period = ReportingPeriod.objects.filter(
                    organization__parent=org
                ).order_by('-end_date').first()
            
            if not reporting_period:
                problem = {
                    'type': f"{settings.PROBLEM_BASE_URL}/not-found",
                    'title': 'Reporting period not found',
                    'detail': 'No reporting period found',
                }
                return problem_response(problem, status.HTTP_404_NOT_FOUND)
            
            use_weighted = request.query_params.get('weighted', 'false').lower() == 'true'
            esg_score = calculate_group_esg_score(org, reporting_period, use_weighted)
            serializer = ESGScoreSerializer(esg_score)
            
            return success_response(
                data=serializer.data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            problem = {
                'type': f"{settings.PROBLEM_BASE_URL}/server-error",
                'title': 'Server error',
                'detail': f"Error fetching ESG score: {str(e)}",
            }
            return problem_response(problem, status.HTTP_500_INTERNAL_SERVER_ERROR)


class GroupGapsView(APIView):
    """
    Get aggregated compliance gaps.
    
    GET /api/v1/group/top-gaps/
    """
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def get(self, request):
        org = getattr(request, 'organization', None)
        
        if not org or org.organization_type not in ['group']:
            problem = {
                'type': f"{settings.PROBLEM_BASE_URL}/group-not-found",
                'title': 'Group organization not found',
                'detail': 'Group organization not found',
            }
            return problem_response(problem, status.HTTP_400_BAD_REQUEST)
        
        try:
            limit = int(request.query_params.get('limit', 10))
            gaps = get_group_top_gaps(org, limit=limit)
            serializer = ComplianceGapSerializer(gaps, many=True)
            
            return success_response(
                data=serializer.data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            problem = {
                'type': f"{settings.PROBLEM_BASE_URL}/server-error",
                'title': 'Server error',
                'detail': f"Error fetching gaps: {str(e)}",
            }
            return problem_response(problem, status.HTTP_500_INTERNAL_SERVER_ERROR)


class GroupRecommendationsView(APIView):
    """
    Get aggregated recommendations.
    
    GET /api/v1/group/recommendations/
    """
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def get(self, request):
        org = getattr(request, 'organization', None)
        
        if not org or org.organization_type not in ['group']:
            problem = {
                'type': f"{settings.PROBLEM_BASE_URL}/group-not-found",
                'title': 'Group organization not found',
                'detail': 'Group organization not found',
            }
            return problem_response(problem, status.HTTP_400_BAD_REQUEST)
        
        try:
            limit = int(request.query_params.get('limit', 10))
            recommendations = get_group_recommendations(org, limit=limit)
            serializer = ComplianceRecommendationSerializer(recommendations, many=True)
            
            return success_response(
                data=serializer.data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            problem = {
                'type': f"{settings.PROBLEM_BASE_URL}/server-error",
                'title': 'Server error',
                'detail': f"Error fetching recommendations: {str(e)}",
            }
            return problem_response(problem, status.HTTP_500_INTERNAL_SERVER_ERROR)


class SubsidiaryRankingView(APIView):
    """
    Get subsidiary ranking by ESG score.
    
    GET /api/v1/group/subsidiaries/
    """
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def get(self, request):
        org = getattr(request, 'organization', None)
        
        if not org or org.organization_type not in ['group']:
            problem = {
                'type': f"{settings.PROBLEM_BASE_URL}/group-not-found",
                'title': 'Group organization not found',
                'detail': 'Group organization not found',
            }
            return problem_response(problem, status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get reporting period
            period_id = request.query_params.get('reporting_period_id')
            reporting_period = None
            
            if period_id:
                reporting_period = ReportingPeriod.objects.filter(id=period_id).first()
            
            ranking = get_subsidiary_ranking(org, reporting_period)
            serializer = SubsidiaryRankingSerializer(ranking, many=True)
            
            return success_response(
                data=serializer.data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            problem = {
                'type': f"{settings.PROBLEM_BASE_URL}/server-error",
                'title': 'Server error',
                'detail': f"Error fetching ranking: {str(e)}",
            }
            return problem_response(problem, status.HTTP_500_INTERNAL_SERVER_ERROR)


class SubsidiaryComparisonView(APIView):
    """
    Get subsidiary comparison view.
    
    GET /api/v1/group/comparison/
    """
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def get(self, request):
        org = getattr(request, 'organization', None)
        
        if not org or org.organization_type not in ['group']:
            problem = {
                'type': f"{settings.PROBLEM_BASE_URL}/group-not-found",
                'title': 'Group organization not found',
                'detail': 'Group organization not found',
            }
            return problem_response(problem, status.HTTP_400_BAD_REQUEST)
        
        try:
            period_id = request.query_params.get('reporting_period_id')
            reporting_period = None
            
            if period_id:
                reporting_period = ReportingPeriod.objects.filter(id=period_id).first()
            
            comparison = get_subsidiary_comparison(org, reporting_period)
            serializer = SubsidiaryComparisonSerializer(comparison)
            
            return success_response(
                data=serializer.data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            problem = {
                'type': f"{settings.PROBLEM_BASE_URL}/server-error",
                'title': 'Server error',
                'detail': f"Error fetching comparison: {str(e)}",
            }
            return problem_response(problem, status.HTTP_500_INTERNAL_SERVER_ERROR)


class PortfolioSummaryView(APIView):
    """
    Get portfolio summary for investor reporting.
    
    GET /api/v1/group/portfolio-summary/
    """
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def get(self, request):
        org = getattr(request, 'organization', None)
        
        if not org or org.organization_type not in ['group']:
            problem = {
                'type': f"{settings.PROBLEM_BASE_URL}/group-not-found",
                'title': 'Group organization not found',
                'detail': 'Group organization not found',
            }
            return problem_response(problem, status.HTTP_400_BAD_REQUEST)
        
        try:
            summary = get_group_portfolio_summary(org)
            serializer = PortfolioSummarySerializer(summary)
            
            return success_response(
                data=serializer.data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            problem = {
                'type': f"{settings.PROBLEM_BASE_URL}/server-error",
                'title': 'Server error',
                'detail': f"Error fetching portfolio summary: {str(e)}",
            }
            return problem_response(problem, status.HTTP_500_INTERNAL_SERVER_ERROR)
