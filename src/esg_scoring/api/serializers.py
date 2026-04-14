"""ESG Scoring API Serializers - Validation and response formatting."""
from rest_framework import serializers
from datetime import datetime

from esg_scoring.models import IndicatorScore, PillarScore, ESGScore
from indicators.models import Indicator
from submissions.models import ReportingPeriod


class IndicatorScoreSerializer(serializers.ModelSerializer):
    """Serializer for individual indicator scores."""
    
    indicator_name = serializers.CharField(source='indicator.name', read_only=True)
    period_name = serializers.CharField(source='reporting_period.name', read_only=True)
    
    class Meta:
        model = IndicatorScore
        fields = (
            'id',
            'organization',
            'indicator',
            'indicator_name',
            'reporting_period',
            'period_name',
            'score',
            'value',
            'target',
            'baseline',
            'progress',
            'status',
            'calculation_method',
            'is_manual',
            'note',
            'calculated_at',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'score',
            'progress',
            'status',
            'calculated_at',
            'created_at',
            'updated_at',
        )


class IndicatorScoreDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for indicator scores with full relationships."""
    
    indicator = serializers.SerializerMethodField()
    period = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    
    class Meta:
        model = IndicatorScore
        fields = (
            'id',
            'organization',
            'indicator',
            'period',
            'score',
            'value',
            'target',
            'baseline',
            'progress',
            'status',
            'is_on_track',
            'is_at_risk',
            'calculation_method',
            'is_manual',
            'note',
            'calculated_at',
        )
    
    def get_indicator(self, obj):
        return {
            'id': str(obj.indicator.id),
            'name': obj.indicator.name,
            'pillar': obj.indicator.pillar,
            'direction': obj.indicator.direction,
        }
    
    def get_period(self, obj):
        return {
            'id': str(obj.reporting_period.id),
            'name': obj.reporting_period.name,
            'start_date': obj.reporting_period.start_date.isoformat(),
            'end_date': obj.reporting_period.end_date.isoformat(),
        }
    
    def get_organization(self, obj):
        return {
            'id': str(obj.organization.id),
            'name': obj.organization.name,
        }


class PillarScoreSerializer(serializers.ModelSerializer):
    """Serializer for pillar (E/S/G) scores."""
    
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    period_name = serializers.CharField(source='reporting_period.name', read_only=True)
    health_status = serializers.SerializerMethodField()
    risk_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = PillarScore
        fields = (
            'id',
            'organization',
            'organization_name',
            'reporting_period',
            'period_name',
            'pillar',
            'score',
            'indicator_count',
            'on_track_count',
            'at_risk_count',
            'health_status',
            'risk_percentage',
            'is_dirty',
            'calculated_at',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'score',
            'calculated_at',
            'created_at',
            'updated_at',
        )
    
    def get_health_status(self, obj):
        return obj.get_health_status()
    
    def get_risk_percentage(self, obj):
        return obj.get_risk_percentage()


class ESGScoreSerializer(serializers.ModelSerializer):
    """Serializer for overall ESG scores."""
    
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    period_name = serializers.CharField(source='reporting_period.name', read_only=True)
    strengths = serializers.SerializerMethodField()
    weaknesses = serializers.SerializerMethodField()
    pillar_ranking = serializers.SerializerMethodField()
    
    class Meta:
        model = ESGScore
        fields = (
            'id',
            'organization',
            'organization_name',
            'reporting_period',
            'period_name',
            'environmental_score',
            'social_score',
            'governance_score',
            'overall_score',
            'environmental_weight',
            'social_weight',
            'governance_weight',
            'strengths',
            'weaknesses',
            'pillar_ranking',
            'is_consolidated',
            'is_dirty',
            'calculated_at',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'overall_score',
            'strengths',
            'weaknesses',
            'pillar_ranking',
            'calculated_at',
            'created_at',
            'updated_at',
        )
    
    def get_strengths(self, obj):
        strengths = obj.get_strengths()
        return list(strengths.items())
    
    def get_weaknesses(self, obj):
        weaknesses = obj.get_weaknesses()
        return list(weaknesses.items())
    
    def get_pillar_ranking(self, obj):
        ranking = obj.get_pillar_ranking()
        return list(ranking)


class ScoreSummarySerializer(serializers.Serializer):
    """Serializer for ESG score summary for frontend."""
    
    organization_id = serializers.CharField()
    organization_name = serializers.CharField()
    period_id = serializers.CharField()
    period_name = serializers.CharField()
    overall = serializers.FloatField()
    environmental = serializers.FloatField()
    social = serializers.FloatField()
    governance = serializers.FloatField()
    strengths = serializers.ListField(child=serializers.DictField())
    weaknesses = serializers.ListField(child=serializers.DictField())
    ranking = serializers.ListField(child=serializers.CharField())
    calculated_at = serializers.DateTimeField()


class CalculateScoreSerializer(serializers.Serializer):
    """Serializer for triggering score calculation."""
    
    organization_id = serializers.CharField(required=False)
    period_id = serializers.CharField(required=False)
    indicator_id = serializers.CharField(required=False)
    pillar = serializers.CharField(required=False)
    weights = serializers.JSONField(required=False)
    include_subsidiaries = serializers.BooleanField(default=False)


class ScoreTrendSerializer(serializers.Serializer):
    """Serializer for score trends."""
    
    period = serializers.CharField()
    start_date = serializers.CharField()
    end_date = serializers.CharField()
    overall = serializers.FloatField()
    environmental = serializers.FloatField()
    social = serializers.FloatField()
    governance = serializers.FloatField()
    calculated_at = serializers.CharField()


class ScoreTrendDataSerializer(serializers.Serializer):
    """Serializer for score trend analysis."""
    
    organization = serializers.CharField()
    name = serializers.CharField()
    trend = ScoreTrendSerializer(many=True)
    has_data = serializers.BooleanField()
    statistics = serializers.DictField(required=False)


class GroupScoreSummarySerializer(serializers.Serializer):
    """Serializer for group score breakdown."""
    
    group = serializers.DictField()
    subsidiaries = serializers.ListField(child=serializers.DictField())
    subsidiary_count = serializers.IntegerField()
    calculated_at = serializers.CharField()


class SubsidiaryPerformanceSerializer(serializers.Serializer):
    """Serializer for subsidiary performance."""
    
    organization = serializers.CharField()
    name = serializers.CharField()
    overall_score = serializers.FloatField()
    environmental = serializers.FloatField()
    social = serializers.FloatField()
    governance = serializers.FloatField()
