"""Serializers for Compliance Intelligence Models."""
from rest_framework import serializers

from compliance.models import (
    FrameworkReadiness,
    ComplianceGapPriority,
    ComplianceRecommendation,
)


class FrameworkReadinessSerializer(serializers.ModelSerializer):
    """Serializer for Framework Readiness."""
    
    organization_name = serializers.CharField(source="organization.name", read_only=True)
    framework_code = serializers.CharField(source="framework.code", read_only=True)
    framework_name = serializers.CharField(source="framework.name", read_only=True)
    risk_label = serializers.CharField(source="get_risk_level_display", read_only=True)
    
    class Meta:
        model = FrameworkReadiness
        fields = [
            "id",
            "organization",
            "organization_name",
            "framework",
            "framework_code",
            "framework_name",
            "reporting_period",
            "total_requirements",
            "covered_requirements",
            "coverage_percent",
            "mandatory_requirements",
            "mandatory_covered",
            "mandatory_coverage_percent",
            "readiness_score",
            "risk_level",
            "risk_label",
            "is_current",
            "calculated_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "organization_name",
            "framework_code",
            "framework_name",
            "risk_label",
            "calculated_at",
            "created_at",
        ]


class FrameworkReadinessSummarySerializer(serializers.Serializer):
    """Summary view of readiness for dashboard."""
    
    framework_code = serializers.CharField()
    framework_name = serializers.CharField()
    readiness_score = serializers.FloatField()
    coverage_percent = serializers.FloatField()
    mandatory_coverage_percent = serializers.FloatField()
    risk_level = serializers.CharField()
    is_on_track = serializers.BooleanField()
    is_at_risk = serializers.BooleanField()
    is_critical = serializers.BooleanField()
    uncovered_count = serializers.IntegerField()
    mandatory_gap_count = serializers.IntegerField()


class ComplianceGapPrioritySerializer(serializers.ModelSerializer):
    """Serializer for Compliance Gap Priority."""
    
    organization_name = serializers.CharField(source="organization.name", read_only=True)
    framework_code = serializers.CharField(source="framework.code", read_only=True)
    requirement_code = serializers.CharField(source="requirement.code", read_only=True)
    requirement_title = serializers.CharField(source="requirement.title", read_only=True)
    requirement_mandatory = serializers.BooleanField(
        source="requirement.is_mandatory", read_only=True
    )
    priority_label = serializers.CharField(source="get_priority_level_display", read_only=True)
    impact_label = serializers.CharField(source="get_impact_category_display", read_only=True)
    
    class Meta:
        model = ComplianceGapPriority
        fields = [
            "id",
            "organization",
            "organization_name",
            "framework",
            "framework_code",
            "requirement",
            "requirement_code",
            "requirement_title",
            "requirement_mandatory",
            "mandatory_weight",
            "framework_weight",
            "pillar_weight",
            "coverage_impact_weight",
            "priority_score",
            "priority_level",
            "priority_label",
            "impact_category",
            "impact_label",
            "gap_description",
            "efforts_to_close",
            "estimated_effort_days",
            "is_active",
            "last_assessed_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "organization_name",
            "framework_code",
            "requirement_code",
            "requirement_title",
            "requirement_mandatory",
            "priority_label",
            "impact_label",
            "last_assessed_at",
            "created_at",
        ]


class ComplianceGapPrioritySummarySerializer(serializers.Serializer):
    """Summary view of priority gaps."""
    
    requirement_code = serializers.CharField()
    requirement_title = serializers.CharField()
    priority_score = serializers.FloatField()
    priority_level = serializers.CharField()
    is_mandatory = serializers.BooleanField()
    estimated_effort_days = serializers.IntegerField()
    efforts_to_close = serializers.CharField()


class ComplianceRecommendationSerializer(serializers.ModelSerializer):
    """Serializer for Compliance Recommendations."""
    
    organization_name = serializers.CharField(source="organization.name", read_only=True)
    framework_code = serializers.CharField(source="framework.code", read_only=True)
    requirement_code = serializers.CharField(source="requirement.code", read_only=True)
    requirement_title = serializers.CharField(source="requirement.title", read_only=True)
    priority_label = serializers.CharField(source="get_priority_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    type_label = serializers.CharField(source="get_recommendation_type_display", read_only=True)
    effort_text = serializers.SerializerMethodField()
    is_high_impact = serializers.SerializerMethodField()
    
    class Meta:
        model = ComplianceRecommendation
        fields = [
            "id",
            "organization",
            "organization_name",
            "framework",
            "framework_code",
            "requirement",
            "requirement_code",
            "requirement_title",
            "title",
            "description",
            "recommendation_type",
            "type_label",
            "actionable_steps",
            "impact_score",
            "is_high_impact",
            "priority",
            "priority_label",
            "estimated_effort_days",
            "effort_text",
            "required_resources",
            "dependencies",
            "status",
            "status_label",
            "started_at",
            "completed_at",
            "internal_notes",
            "generated_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "organization_name",
            "framework_code",
            "requirement_code",
            "requirement_title",
            "priority_label",
            "status_label",
            "type_label",
            "generated_at",
            "created_at",
        ]
    
    def get_effort_text(self, obj):
        return obj.get_effort_estimate_text()
    
    def get_is_high_impact(self, obj):
        return obj.is_high_impact()


class ComplianceRecommendationDetailSerializer(ComplianceRecommendationSerializer):
    """Detailed serializer for recommendations with extra fields."""
    
    class Meta(ComplianceRecommendationSerializer.Meta):
        pass


class ComplianceRecommendationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating recommendations."""
    
    class Meta:
        model = ComplianceRecommendation
        fields = [
            "organization",
            "framework",
            "requirement",
            "title",
            "description",
            "recommendation_type",
            "actionable_steps",
            "impact_score",
            "priority",
            "estimated_effort_days",
            "required_resources",
        ]


class ReadinessDashboardSerializer(serializers.Serializer):
    """Dashboard view combining readiness and gaps."""
    
    organization_id = serializers.IntegerField()
    total_frameworks = serializers.IntegerField()
    frameworks_on_track = serializers.IntegerField()
    frameworks_at_risk = serializers.IntegerField()
    frameworks_critical = serializers.IntegerField()
    avg_readiness_score = serializers.FloatField()
    total_gaps = serializers.IntegerField()
    high_priority_gaps = serializers.IntegerField()
    pending_recommendations = serializers.IntegerField()
    in_progress_recommendations = serializers.IntegerField()
    readiness_by_framework = FrameworkReadinessSummarySerializer(many=True, read_only=True)
    top_gaps = ComplianceGapPrioritySummarySerializer(many=True, read_only=True)
    top_recommendations = ComplianceRecommendationSerializer(many=True, read_only=True)


class GapAnalysisResponseSerializer(serializers.Serializer):
    """Response for gap analysis queries."""
    
    organization_id = serializers.IntegerField()
    framework_code = serializers.CharField()
    framework_name = serializers.CharField()
    total_requirements = serializers.IntegerField()
    covered_requirements = serializers.IntegerField()
    coverage_percent = serializers.FloatField()
    readiness_score = serializers.FloatField()
    gaps = ComplianceGapPrioritySummarySerializer(many=True)
