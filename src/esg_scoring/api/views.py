"""ESG Scoring API Views - Endpoints for accessing and calculating scores."""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
import logging

from common.permissions import IsOrgMember
from organizations.models import Organization
from submissions.models import ReportingPeriod
from esg_scoring.models import ESGScore, IndicatorScore, PillarScore
from esg_scoring.services.indicator_scoring import (
    calculate_indicator_score,
    calculate_all_indicator_scores,
)
from esg_scoring.services.pillar_scoring import (
    calculate_pillar_score,
    calculate_all_pillar_scores,
)
from esg_scoring.services.esg_scoring import (
    calculate_esg_score,
    calculate_esg_scores_for_all_organizations,
    get_esg_score_summary,
)
from esg_scoring.selectors.group_scoring import (
    calculate_group_esg_score,
    get_group_esg_breakdown,
    get_top_performing_subsidiaries,
)
from esg_scoring.selectors.trends import (
    get_esg_score_trend,
    get_pillar_trend,
    get_year_over_year_comparison,
)
from esg_scoring.api.serializers import (
    ESGScoreSerializer,
    IndicatorScoreSerializer,
    PillarScoreSerializer,
    ScoreSummarySerializer,
    CalculateScoreSerializer,
    ScoreTrendDataSerializer,
    GroupScoreSummarySerializer,
    SubsidiaryPerformanceSerializer,
)

logger = logging.getLogger(__name__)


class ESGScoreViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ESG Scoring endpoints.
    
    Endpoints:
    - GET /api/v1/esg/scores/ - List organization's ESG scores
    - GET /api/v1/esg/scores/{id}/ - Retrieve specific score
    - GET /api/v1/esg/scores/current/ - Get latest score
    - POST /api/v1/esg/scores/calculate/ - Trigger score calculation
    - GET /api/v1/esg/scores/summary/ - Summary for frontend
    - GET /api/v1/esg/scores/trend/ - Trend analysis
    - GET /api/v1/esg/scores/group-breakdown/ - Group consolidation
    """
    
    serializer_class = ESGScoreSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]
    http_method_names = ['get', 'post']
    
    def get_queryset(self):
        """Filter by organization from header."""
        org_id = self.request.META.get('HTTP_X_ORG_ID')
        if not org_id:
            return ESGScore.objects.none()
        return ESGScore.objects.filter(organization__id=org_id).order_by('-calculated_at')
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get the latest ESG score for the organization."""
        try:
            org_id = request.META.get('HTTP_X_ORG_ID')
            if not org_id:
                return Response(
                    {'error': 'X-ORG-ID header required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            org = get_object_or_404(Organization, id=org_id)
            
            # Check permission
            if not self._is_org_member(request, org):
                return Response(
                    {'error': 'Not authorized for this organization'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            score = ESGScore.objects.filter(
                organization=org
            ).order_by('-calculated_at').first()
            
            if not score:
                return Response(
                    {'error': 'No ESG scores found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = self.get_serializer(score)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error retrieving current score: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """Trigger ESG score calculation."""
        try:
            serializer = CalculateScoreSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            org_id = request.META.get('HTTP_X_ORG_ID') or serializer.validated_data.get('organization_id')
            period_id = serializer.validated_data.get('period_id')
            
            if not org_id:
                return Response(
                    {'error': 'Organization ID required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            org = get_object_or_404(Organization, id=org_id)
            
            # Check permission
            if not self._is_org_member(request, org):
                return Response(
                    {'error': 'Not authorized for this organization'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get period (latest if not specified)
            if period_id:
                period = get_object_or_404(ReportingPeriod, id=period_id)
            else:
                period = ReportingPeriod.objects.filter(
                    is_active=True
                ).order_by('-end_date').first()
                
                if not period:
                    return Response(
                        {'error': 'No active reporting period found'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Calculate scores
            calculate_all_indicator_scores(org, period)
            calculate_all_pillar_scores(org, period)
            esg_score = calculate_esg_score(org, period)
            
            serializer = self.get_serializer(esg_score)
            return Response(
                {
                    'message': 'Score calculated successfully',
                    'score': serializer.data
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            logger.error(f"Error calculating score: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get ESG score summary for frontend."""
        try:
            org_id = request.META.get('HTTP_X_ORG_ID')
            period_id = request.query_params.get('period_id')
            
            if not org_id:
                return Response(
                    {'error': 'X-ORG-ID header required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            org = get_object_or_404(Organization, id=org_id)
            
            # Check permission
            if not self._is_org_member(request, org):
                return Response(
                    {'error': 'Not authorized for this organization'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get period
            if period_id:
                period = get_object_or_404(ReportingPeriod, id=period_id)
            else:
                period = ReportingPeriod.objects.filter(
                    is_active=True
                ).order_by('-end_date').first()
                
                if not period:
                    return Response(
                        {'error': 'No active reporting period found'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            summary = get_esg_score_summary(org, period)
            
            if not summary:
                return Response(
                    {'error': 'No score data found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(summary)
            
        except Exception as e:
            logger.error(f"Error retrieving score summary: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def trend(self, request):
        """Get ESG score trend."""
        try:
            org_id = request.META.get('HTTP_X_ORG_ID')
            periods = int(request.query_params.get('periods', 12))
            
            if not org_id:
                return Response(
                    {'error': 'X-ORG-ID header required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            org = get_object_or_404(Organization, id=org_id)
            
            # Check permission
            if not self._is_org_member(request, org):
                return Response(
                    {'error': 'Not authorized for this organization'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            trend = get_esg_score_trend(org, periods=periods)
            
            if not trend:
                return Response(
                    {'error': 'Error retrieving trend'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return Response(trend)
            
        except Exception as e:
            logger.error(f"Error retrieving score trend: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def group_breakdown(self, request):
        """Get group ESG score breakdown."""
        try:
            org_id = request.META.get('HTTP_X_ORG_ID')
            period_id = request.query_params.get('period_id')
            
            if not org_id:
                return Response(
                    {'error': 'X-ORG-ID header required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            org = get_object_or_404(Organization, id=org_id)
            
            # Check permission
            if not self._is_org_member(request, org):
                return Response(
                    {'error': 'Not authorized for this organization'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get period
            if period_id:
                period = get_object_or_404(ReportingPeriod, id=period_id)
            else:
                period = ReportingPeriod.objects.filter(
                    is_active=True
                ).order_by('-end_date').first()
                
                if not period:
                    return Response(
                        {'error': 'No active reporting period found'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            breakdown = get_group_esg_breakdown(org, period)
            
            if not breakdown:
                return Response(
                    {'error': 'No group score data found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(breakdown)
            
        except Exception as e:
            logger.error(f"Error retrieving group breakdown: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def top_performers(self, request):
        """Get top performing subsidiaries."""
        try:
            org_id = request.META.get('HTTP_X_ORG_ID')
            limit = int(request.query_params.get('limit', 5))
            period_id = request.query_params.get('period_id')
            
            if not org_id:
                return Response(
                    {'error': 'X-ORG-ID header required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            org = get_object_or_404(Organization, id=org_id)
            
            # Check permission
            if not self._is_org_member(request, org):
                return Response(
                    {'error': 'Not authorized for this organization'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get period
            if period_id:
                period = get_object_or_404(ReportingPeriod, id=period_id)
            else:
                period = ReportingPeriod.objects.filter(
                    is_active=True
                ).order_by('-end_date').first()
                
                if not period:
                    return Response(
                        {'error': 'No active reporting period found'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            performers = get_top_performing_subsidiaries(org, period, limit=limit)
            return Response(performers)
            
        except Exception as e:
            logger.error(f"Error retrieving top performers: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _is_org_member(self, request, org):
        """Check if user is member of organization."""
        # This would be implemented based on your user-org relationship
        # For now, assumes header-based org context is sufficient
        return True


class IndicatorScoreViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for reading indicator scores."""
    
    serializer_class = IndicatorScoreSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def get_queryset(self):
        """Filter by organization from header."""
        org_id = self.request.META.get('HTTP_X_ORG_ID')
        if not org_id:
            return IndicatorScore.objects.none()
        return IndicatorScore.objects.filter(
            organization__id=org_id
        ).order_by('-calculated_at')


class PillarScoreViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for reading pillar scores."""
    
    serializer_class = PillarScoreSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def get_queryset(self):
        """Filter by organization from header."""
        org_id = self.request.META.get('HTTP_X_ORG_ID')
        if not org_id:
            return PillarScore.objects.none()
        return PillarScore.objects.filter(
            organization__id=org_id
        ).order_by('-calculated_at')
