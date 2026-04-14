"""API Views for Compliance Intelligence Engine."""
from django.db.models import Q, Avg, Count
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from compliance.models import (
    FrameworkReadiness,
    ComplianceGapPriority,
    ComplianceRecommendation,
)
from compliance.services import (
    calculate_framework_readiness,
    calculate_all_framework_readiness,
    calculate_gap_priority,
    get_top_priority_gaps,
    generate_recommendations,
    get_recommendations_by_priority,
    get_recommendations_summary,
)
from .compliance_intelligence_serializers import (
    FrameworkReadinessSerializer,
    FrameworkReadinessSummarySerializer,
    ComplianceGapPrioritySerializer,
    ComplianceRecommendationSerializer,
    ReadinessDashboardSerializer,
    GapAnalysisResponseSerializer,
)


class FrameworkReadinessViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for Framework Readiness assessment.
    
    List all readiness scores for organization (filtered by X-ORG-ID header).
    """
    
    serializer_class = FrameworkReadinessSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["framework", "risk_level", "is_current"]
    ordering_fields = ["-readiness_score", "-calculated_at", "framework"]
    
    def get_queryset(self):
        """Get readiness scores for current organization."""
        org_id = self.request.headers.get("X-ORG-ID")
        return FrameworkReadiness.objects.filter(
            organization_id=org_id,
            is_current=True,
        ).order_by("-readiness_score")
    
    @extend_schema(
        summary="Get readiness summary by risk level",
        responses=FrameworkReadinessSummarySerializer(many=True),
    )
    @action(detail=False, methods=["get"])
    def by_risk_level(self, request):
        """Get readiness scores grouped and sorted by risk level."""
        org_id = request.headers.get("X-ORG-ID")
        readiness_scores = FrameworkReadiness.objects.filter(
            organization_id=org_id,
            is_current=True,
        ).values("risk_level").annotate(
            count=Count("id"),
            avg_score=Avg("readiness_score"),
        ).order_by("-avg_score")
        
        return Response(readiness_scores)
    
    @extend_schema(
        summary="Recalculate readiness for organization",
        responses=FrameworkReadinessSerializer(many=True),
    )
    @action(detail=False, methods=["post"])
    def recalculate(self, request):
        """Trigger readiness recalculation for all frameworks."""
        from organizations.models import Organization
        from submissions.models import ReportingPeriod
        
        org_id = request.headers.get("X-ORG-ID")
        
        try:
            org = Organization.objects.get(id=org_id)
            # Get current reporting period
            period = ReportingPeriod.objects.filter(
                is_active=True,
                organization=org
            ).first()
            
            if not period:
                return Response(
                    {"error": "No active reporting period"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            readiness_scores = calculate_all_framework_readiness(org, period)
            serializer = FrameworkReadinessSerializer(readiness_scores, many=True)
            
            return Response({
                "message": f"Recalculated readiness for {len(readiness_scores)} frameworks",
                "results": serializer.data
            })
        except Organization.DoesNotExist:
            return Response(
                {"error": "Organization not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class ComplianceGapPriorityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for Compliance Gap prioritization.
    
    List all prioritized gaps for organization.
    """
    
    serializer_class = ComplianceGapPrioritySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["framework", "priority_level", "impact_category", "is_active"]
    ordering_fields = ["-priority_score", "priority_level", "impact_category"]
    
    def get_queryset(self):
        """Get gaps for current organization."""
        org_id = self.request.headers.get("X-ORG-ID")
        return ComplianceGapPriority.objects.filter(
            organization_id=org_id,
            is_active=True,
        ).order_by("-priority_score")
    
    @extend_schema(
        summary="Get top priority gaps",
        responses=ComplianceGapPrioritySerializer(many=True),
    )
    @action(detail=False, methods=["get"])
    def top_gaps(self, request):
        """Get top 10 priority gaps."""
        from organizations.models import Organization
        
        org_id = request.headers.get("X-ORG-ID")
        org = Organization.objects.get(id=org_id)
        
        gaps = get_top_priority_gaps(org, limit=10)
        serializer = ComplianceGapPrioritySerializer(gaps, many=True)
        
        return Response(serializer.data)
    
    @extend_schema(
        summary="Get gaps for specific framework",
        responses=ComplianceGapPrioritySerializer(many=True),
    )
    @action(detail=False, methods=["get"])
    def by_framework(self, request):
        """Get gaps filtered by framework."""
        framework_id = request.query_params.get("framework_id")
        org_id = request.headers.get("X-ORG-ID")
        
        gaps = ComplianceGapPriority.objects.filter(
            organization_id=org_id,
            framework_id=framework_id,
            is_active=True,
        ).order_by("-priority_score")
        
        serializer = ComplianceGapPrioritySerializer(gaps, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Recalculate gap priorities",
        responses=ComplianceGapPrioritySerializer(many=True),
    )
    @action(detail=False, methods=["post"])
    def recalculate(self, request):
        """Trigger gap priority recalculation."""
        from organizations.models import Organization
        
        org_id = request.headers.get("X-ORG-ID")
        org = Organization.objects.get(id=org_id)
        
        result = {}
        org_frameworks = org.organization_frameworks.filter(is_enabled=True)
        
        for org_framework in org_frameworks:
            gaps = calculate_gap_priority(org, org_framework.framework)
            result[org_framework.framework.code] = len(gaps)
        
        return Response({
            "message": "Recalculated gap priorities",
            "frameworks_processed": len(org_frameworks),
            "results": result
        })


class ComplianceRecommendationViewSet(viewsets.ModelViewSet):
    """
    API endpoints for Compliance Recommendations.
    
    List, create, and manage compliance recommendations.
    """
    
    serializer_class = ComplianceRecommendationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["framework", "recommendation_type", "priority", "status"]
    ordering_fields = ["-priority", "-impact_score", "status"]
    
    def get_queryset(self):
        """Get recommendations for current organization."""
        org_id = self.request.headers.get("X-ORG-ID")
        return ComplianceRecommendation.objects.filter(
            organization_id=org_id,
        ).order_by("-priority", "-impact_score")
    
    @extend_schema(
        summary="Get high-impact pending recommendations",
        responses=ComplianceRecommendationSerializer(many=True),
    )
    @action(detail=False, methods=["get"])
    def high_priority_pending(self, request):
        """Get high-priority pending recommendations."""
        org_id = request.headers.get("X-ORG-ID")
        
        recs = ComplianceRecommendation.objects.filter(
            organization_id=org_id,
            status="pending",
            priority="high",
        ).order_by("-impact_score")[:20]
        
        serializer = ComplianceRecommendationSerializer(recs, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Get recommendations by priority",
        responses=ComplianceRecommendationSerializer(many=True),
    )
    @action(detail=False, methods=["get"])
    def by_priority(self, request):
        """Get recommendations filtered by priority."""
        priority = request.query_params.get("priority")
        org_id = request.headers.get("X-ORG-ID")
        
        recs = get_recommendations_by_priority(
            organization_id=org_id,
            priority=priority
        )
        
        serializer = ComplianceRecommendationSerializer(recs, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Get recommendation summary",
        responses={"type": "object"},
    )
    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Get summary of all recommendations."""
        from organizations.models import Organization
        
        org_id = request.headers.get("X-ORG-ID")
        org = Organization.objects.get(id=org_id)
        
        summary = get_recommendations_summary(org)
        return Response(summary)
    
    @extend_schema(
        summary="Mark recommendation as in progress",
        responses=ComplianceRecommendationSerializer,
    )
    @action(detail=True, methods=["post"])
    def mark_in_progress(self, request, pk=None):
        """Mark a recommendation as in progress."""
        rec = self.get_object()
        rec.mark_in_progress()
        
        serializer = ComplianceRecommendationSerializer(rec)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Mark recommendation as completed",
        responses=ComplianceRecommendationSerializer,
    )
    @action(detail=True, methods=["post"])
    def mark_completed(self, request, pk=None):
        """Mark a recommendation as completed."""
        rec = self.get_object()
        rec.mark_completed()
        
        serializer = ComplianceRecommendationSerializer(rec)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Generate recommendations",
        responses=ComplianceRecommendationSerializer(many=True),
    )
    @action(detail=False, methods=["post"])
    def generate(self, request):
        """Generate recommendations for organization."""
        from organizations.models import Organization, RegulatoryFramework
        
        org_id = request.headers.get("X-ORG-ID")
        framework_id = request.data.get("framework_id")
        
        org = Organization.objects.get(id=org_id)
        framework = RegulatoryFramework.objects.get(id=framework_id)
        
        recs = generate_recommendations(org, framework)
        serializer = ComplianceRecommendationSerializer(recs, many=True)
        
        return Response({
            "message": f"Generated {len(recs)} recommendations",
            "recommendations": serializer.data
        })


class ComplianceIntelligenceDashboardViewSet(viewsets.ViewSet):
    """
    Dashboard endpoints combining readiness, gaps, and recommendations.
    """
    
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get compliance intelligence dashboard",
        responses={"type": "object"},
    )
    @action(detail=False, methods=["get"], url_path="dashboard")
    def dashboard(self, request):
        """Get comprehensive compliance dashboard."""
        from organizations.models import Organization
        
        org_id = request.headers.get("X-ORG-ID")
        org = Organization.objects.get(id=org_id)
        
        # Get readiness scores
        readiness = FrameworkReadiness.objects.filter(
            organization=org,
            is_current=True,
        )
        
        # Get gaps
        gaps = ComplianceGapPriority.objects.filter(
            organization=org,
            is_active=True,
        )
        
        # Get recommendations
        recs = ComplianceRecommendation.objects.filter(
            organization=org,
        )
        
        dashboard_data = {
            "organization_id": org.id,
            "organization_name": org.name,
            "readiness": {
                "total_frameworks": readiness.count(),
                "frameworks_on_track": readiness.filter(risk_level="low").count(),
                "frameworks_at_risk": readiness.filter(risk_level="medium").count(),
                "frameworks_critical": readiness.filter(risk_level="high").count(),
                "avg_readiness_score": readiness.aggregate(Avg("readiness_score"))["readiness_score__avg"] or 0,
                "frameworks": FrameworkReadinessSerializer(readiness, many=True).data,
            },
            "gaps": {
                "total": gaps.count(),
                "high_priority": gaps.filter(priority_level="high").count(),
                "medium_priority": gaps.filter(priority_level="medium").count(),
                "low_priority": gaps.filter(priority_level="low").count(),
                "top_gaps": ComplianceGapPrioritySerializer(gaps[:10], many=True).data,
            },
            "recommendations": {
                "total": recs.count(),
                "pending": recs.filter(status="pending").count(),
                "in_progress": recs.filter(status="in_progress").count(),
                "completed": recs.filter(status="completed").count(),
                "high_priority": recs.filter(priority="high").count(),
                "top_recommendations": ComplianceRecommendationSerializer(
                    recs.filter(status="pending").order_by("-priority", "-impact_score")[:5],
                    many=True
                ).data,
            }
        }
        
        return Response(dashboard_data)
