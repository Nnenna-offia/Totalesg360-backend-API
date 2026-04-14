"""Serializers for Group Analytics API."""
from rest_framework import serializers
from organizations.models import Organization


class SubsidiaryScoreSerializer(serializers.Serializer):
    """Serializer for individual subsidiary ESG score."""
    org_id = serializers.CharField()
    org_name = serializers.CharField()
    environmental = serializers.FloatField()
    social = serializers.FloatField()
    governance = serializers.FloatField()
    overall = serializers.FloatField()
    weight = serializers.FloatField(allow_null=True)


class ESGScoreSerializer(serializers.Serializer):
    """Serializer for aggregated group ESG score."""
    environmental = serializers.FloatField(allow_null=True)
    social = serializers.FloatField(allow_null=True)
    governance = serializers.FloatField(allow_null=True)
    overall = serializers.FloatField(allow_null=True)
    subsidiary_count = serializers.IntegerField()
    calculation_method = serializers.CharField()
    subsidiaries = SubsidiaryScoreSerializer(many=True)


class ESGTrendSerializer(serializers.Serializer):
    """Serializer for ESG score trends."""
    period = serializers.CharField()
    period_name = serializers.CharField()
    end_date = serializers.DateTimeField()
    environmental = serializers.FloatField(allow_null=True)
    social = serializers.FloatField(allow_null=True)
    governance = serializers.FloatField(allow_null=True)
    overall = serializers.FloatField(allow_null=True)


class SubsidiaryRankingSerializer(serializers.Serializer):
    """Serializer for subsidiary ESG ranking."""
    rank = serializers.IntegerField()
    org_id = serializers.CharField()
    org_name = serializers.CharField()
    environmental = serializers.FloatField()
    social = serializers.FloatField()
    governance = serializers.FloatField()
    overall = serializers.FloatField()
    organization_type = serializers.CharField()
    change = serializers.CharField(allow_null=True)


class FrameworkReadinessOrganizationSerializer(serializers.Serializer):
    """Serializer for organization framework readiness."""
    id = serializers.CharField()
    name = serializers.CharField()
    coverage = serializers.FloatField()
    risk_level = serializers.CharField()
    mandatory_coverage = serializers.FloatField()


class FrameworkReadinessSerializer(serializers.Serializer):
    """Serializer for aggregated framework readiness."""
    code = serializers.CharField()
    name = serializers.CharField()
    avg_readiness = serializers.FloatField()
    risk_level = serializers.CharField()
    subsidiary_count = serializers.IntegerField()
    low_risk_count = serializers.IntegerField()
    medium_risk_count = serializers.IntegerField()
    high_risk_count = serializers.IntegerField()
    subsidiaries = FrameworkReadinessOrganizationSerializer(many=True)


class GroupReadinessResponseSerializer(serializers.Serializer):
    """Serializer for group framework readiness response."""
    frameworks = FrameworkReadinessSerializer(many=True)
    parent_readiness = serializers.JSONField(allow_null=True)
    total_subsidiaries = serializers.IntegerField()


class ReadinessSummarySerializer(serializers.Serializer):
    """Serializer for readiness summary."""
    avg_readiness = serializers.FloatField(allow_null=True)
    risk_level = serializers.CharField()
    total_frameworks = serializers.IntegerField()
    total_organizations = serializers.IntegerField()


class ComplianceGapOrganizationSerializer(serializers.Serializer):
    """Serializer for organization with compliance gap."""
    org_id = serializers.CharField()
    org_name = serializers.CharField()
    gap_priority = serializers.CharField()
    priority_score = serializers.FloatField()


class ComplianceGapSerializer(serializers.Serializer):
    """Serializer for aggregated compliance gap."""
    requirement_id = serializers.CharField()
    requirement_code = serializers.CharField()
    requirement_name = serializers.CharField()
    framework_code = serializers.CharField()
    affected_subsidiaries = serializers.IntegerField()
    priority = serializers.CharField()
    high_priority_count = serializers.IntegerField()
    medium_priority_count = serializers.IntegerField()
    low_priority_count = serializers.IntegerField()
    organizations = ComplianceGapOrganizationSerializer(many=True)


class GapSummarySerializer(serializers.Serializer):
    """Serializer for gap summary."""
    total_gaps = serializers.IntegerField()
    total_unique_requirements = serializers.IntegerField()
    high_priority_count = serializers.IntegerField()
    medium_priority_count = serializers.IntegerField()
    low_priority_count = serializers.IntegerField()
    most_common_gap_code = serializers.CharField(allow_null=True)
    most_common_gap_count = serializers.IntegerField()


class ComplianceRecommendationOrganizationSerializer(serializers.Serializer):
    """Serializer for organization with recommendation."""
    org_id = serializers.CharField()
    org_name = serializers.CharField()
    status = serializers.CharField()
    priority = serializers.CharField()


class ComplianceRecommendationSerializer(serializers.Serializer):
    """Serializer for aggregated compliance recommendation."""
    recommendation_id = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    recommendation_type = serializers.CharField()
    framework_code = serializers.CharField()
    affected_subsidiaries = serializers.IntegerField()
    priority = serializers.CharField()
    high_priority_count = serializers.IntegerField()
    medium_priority_count = serializers.IntegerField()
    low_priority_count = serializers.IntegerField()
    pending_count = serializers.IntegerField()
    in_progress_count = serializers.IntegerField()
    deferred_count = serializers.IntegerField()
    organizations = ComplianceRecommendationOrganizationSerializer(many=True)


class RecommendationSummarySerializer(serializers.Serializer):
    """Serializer for recommendation summary."""
    total_recommendations = serializers.IntegerField()
    high_priority_count = serializers.IntegerField()
    medium_priority_count = serializers.IntegerField()
    low_priority_count = serializers.IntegerField()
    pending_count = serializers.IntegerField()
    in_progress_count = serializers.IntegerField()
    completed_count = serializers.IntegerField()
    deferred_count = serializers.IntegerField()


class ReportingPeriodSerializer(serializers.Serializer):
    """Serializer for reporting period."""
    id = serializers.CharField()
    start_date = serializers.DateTimeField(allow_null=True)
    end_date = serializers.DateTimeField(allow_null=True)


class OrganizationRefSerializer(serializers.Serializer):
    """Serializer for organization reference."""
    id = serializers.CharField()
    name = serializers.CharField()
    type = serializers.CharField()


class GroupDashboardSerializer(serializers.Serializer):
    """Serializer for comprehensive group dashboard."""
    organization = OrganizationRefSerializer()
    reporting_period = ReportingPeriodSerializer(allow_null=True)
    esg_score = ESGScoreSerializer(allow_null=True)
    esg_trend = ESGTrendSerializer(many=True)
    subsidiary_ranking = SubsidiaryRankingSerializer(many=True)
    total_subsidiaries = serializers.IntegerField()
    framework_readiness = GroupReadinessResponseSerializer(allow_null=True)
    readiness_summary = ReadinessSummarySerializer(allow_null=True)
    top_gaps = ComplianceGapSerializer(many=True)
    gap_summary = GapSummarySerializer()
    top_recommendations = ComplianceRecommendationSerializer(many=True)
    recommendation_summary = RecommendationSummarySerializer()


class SubsidiaryComparisonSerializer(serializers.Serializer):
    """Serializer for subsidiary comparison."""
    total_subsidiaries = serializers.IntegerField()
    best_performer = SubsidiaryRankingSerializer(allow_null=True)
    lowest_performer = SubsidiaryRankingSerializer(allow_null=True)
    average_score = serializers.FloatField(allow_null=True)
    rankings = SubsidiaryRankingSerializer(many=True)


class PortfolioSummarySerializer(serializers.Serializer):
    """Serializer for investor portfolio summary."""
    organization_name = serializers.CharField()
    organization_id = serializers.CharField()
    portfolio_size = serializers.IntegerField()
    overall_esg_score = serializers.FloatField(allow_null=True)
    environmental_score = serializers.FloatField(allow_null=True)
    social_score = serializers.FloatField(allow_null=True)
    governance_score = serializers.FloatField(allow_null=True)
    overall_readiness = serializers.FloatField(allow_null=True)
    compliance_gaps_count = serializers.IntegerField()
    high_priority_gaps = serializers.IntegerField()
    pending_recommendations = serializers.IntegerField()
    top_performing_subsidiary = serializers.CharField(allow_null=True)
    top_performing_score = serializers.FloatField(allow_null=True)
