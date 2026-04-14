"""Serializers for framework mapping and compliance requirements."""
from rest_framework import serializers
from organizations.models import RegulatoryFramework, OrganizationFramework
from indicators.models import Indicator
from compliance.models import FrameworkRequirement, IndicatorFrameworkMapping


class RegulatoryFrameworkSerializer(serializers.ModelSerializer):
    """Serializer for Regulatory Framework."""
    
    class Meta:
        model = RegulatoryFramework
        fields = [
            'id', 'code', 'name', 'jurisdiction', 'description', 
            'sector', 'is_active', 'priority'
        ]
        read_only_fields = ['id']


class IndicatorMinimalSerializer(serializers.ModelSerializer):
    """Minimal indicator serializer for use in mappings."""
    
    class Meta:
        model = Indicator
        fields = ['id', 'code', 'name']
        read_only_fields = ['id']


class FrameworkRequirementSerializer(serializers.ModelSerializer):
    """Serializer for Framework Requirements."""
    
    framework_code = serializers.CharField(source='framework.code', read_only=True)
    framework_name = serializers.CharField(source='framework.name', read_only=True)
    pillar_display = serializers.CharField(source='get_pillar_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = FrameworkRequirement
        fields = [
            'id', 'framework', 'framework_code', 'framework_name', 
            'code', 'title', 'description', 'pillar', 'pillar_display',
            'is_mandatory', 'status', 'status_display', 'priority',
            'guidance_url', 'version'
        ]
        read_only_fields = ['id']


class FrameworkRequirementDetailSerializer(FrameworkRequirementSerializer):
    """Detailed serializer for Framework Requirements with indicator mappings."""
    
    indicators_mapped = serializers.SerializerMethodField()
    covered_by_count = serializers.SerializerMethodField()
    
    def get_indicators_mapped(self, obj):
        """Get all indicators mapped to this requirement."""
        mappings = obj.indicator_mappings.filter(is_active=True)
        return IndicatorFrameworkMappingSerializer(mappings, many=True).data
    
    def get_covered_by_count(self, obj):
        """Count of indicators covering this requirement."""
        return obj.indicator_mappings.filter(is_active=True).count()
    
    class Meta(FrameworkRequirementSerializer.Meta):
        fields = FrameworkRequirementSerializer.Meta.fields + [
            'indicators_mapped', 'covered_by_count'
        ]


class IndicatorFrameworkMappingSerializer(serializers.ModelSerializer):
    """Serializer for Indicator-Framework mappings."""
    
    indicator_code = serializers.CharField(source='indicator.code', read_only=True)
    indicator_name = serializers.CharField(source='indicator.name', read_only=True)
    framework_code = serializers.CharField(source='framework.code', read_only=True)
    framework_name = serializers.CharField(source='framework.name', read_only=True)
    requirement_code = serializers.CharField(source='requirement.code', read_only=True)
    requirement_title = serializers.CharField(source='requirement.title', read_only=True)
    mapping_type_display = serializers.CharField(source='get_mapping_type_display', read_only=True)
    coverage_status = serializers.SerializerMethodField()
    
    class Meta:
        model = IndicatorFrameworkMapping
        fields = [
            'id', 'indicator', 'indicator_code', 'indicator_name',
            'framework', 'framework_code', 'framework_name',
            'requirement', 'requirement_code', 'requirement_title',
            'mapping_type', 'mapping_type_display', 'is_primary',
            'rationale', 'coverage_percent', 'coverage_status',
            'is_active', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_coverage_status(self, obj):
        """Get human-readable coverage status."""
        return obj.get_coverage_status()


class IndicatorFrameworkMappingDetailSerializer(IndicatorFrameworkMappingSerializer):
    """Detailed serializer with nested objects."""
    
    indicator = IndicatorMinimalSerializer(read_only=True)
    framework = RegulatoryFrameworkSerializer(read_only=True)
    requirement = FrameworkRequirementSerializer(read_only=True)
    
    class Meta(IndicatorFrameworkMappingSerializer.Meta):
        fields = IndicatorFrameworkMappingSerializer.Meta.fields


class FrameworkCoverageSerializer(serializers.Serializer):
    """Serializer for framework coverage statistics."""
    
    framework = RegulatoryFrameworkSerializer(read_only=True)
    total_requirements = serializers.IntegerField()
    covered_requirements = serializers.IntegerField()
    uncovered_requirements = serializers.IntegerField()
    coverage_percent = serializers.FloatField()
    by_pillar = serializers.DictField()


class OrganizationFrameworkStatusSerializer(serializers.Serializer):
    """Serializer for organization's compliance status across frameworks."""
    
    organization_framework = serializers.SerializerMethodField()
    framework = RegulatoryFrameworkSerializer(read_only=True)
    total_requirements = serializers.IntegerField()
    covered_requirements = serializers.IntegerField()
    uncovered_requirements = serializers.IntegerField()
    coverage_percent = serializers.FloatField()
    is_primary = serializers.BooleanField()
    
    def get_organization_framework(self, obj):
        """Return organization framework relationship."""
        org_fw = obj.get('organization_framework')
        if org_fw:
            return {
                'id': org_fw.id,
                'is_primary': org_fw.is_primary,
                'is_enabled': org_fw.is_enabled,
                'assigned_at': org_fw.assigned_at,
            }
        return None


class IndicatorFrameworksSerializer(serializers.Serializer):
    """Serializer for indicator with all framework mappings."""
    
    indicator = IndicatorMinimalSerializer(read_only=True)
    frameworks = serializers.SerializerMethodField()
    total_frameworks = serializers.SerializerMethodField()
    
    def get_frameworks(self, obj):
        """Get list of frameworks and requirements."""
        indicator = obj.get('indicator')
        if not indicator:
            return []
        
        from compliance.selectors import get_indicator_frameworks
        mappings = get_indicator_frameworks(indicator)
        
        frameworks_map = {}
        for mapping in mappings:
            fw_code = mapping['framework'].code
            if fw_code not in frameworks_map:
                frameworks_map[fw_code] = {
                    'framework': RegulatoryFrameworkSerializer(
                        mapping['framework']
                    ).data,
                    'requirements': []
                }
            
            frameworks_map[fw_code]['requirements'].append({
                'code': mapping['requirement'].code,
                'title': mapping['requirement'].title,
                'mapping_type': mapping['mapping_type'],
                'coverage_status': mapping['coverage_status'],
                'is_primary': mapping['mapping'].is_primary,
            })
        
        return list(frameworks_map.values())
    
    def get_total_frameworks(self, obj):
        """Count unique frameworks."""
        frameworks = self.get_frameworks(obj)
        return len(frameworks)


class FrameworkIndicatorsSerializer(serializers.Serializer):
    """Serializer for framework with all mapped indicators."""
    
    framework = RegulatoryFrameworkSerializer(read_only=True)
    indicators = serializers.SerializerMethodField()
    total_indicators = serializers.SerializerMethodField()
    requirement_coverage = serializers.SerializerMethodField()
    
    def get_indicators(self, obj):
        """Get all indicators mapped to this framework."""
        framework = obj.get('framework')
        if not framework:
            return []
        
        from compliance.selectors import get_framework_indicators
        indicators = get_framework_indicators(framework)
        
        result = []
        for indicator in indicators:
            result.append({
                'indicator': {
                    'id': str(indicator.id),
                    'code': indicator.code,
                    'name': indicator.name,
                    'pillar': indicator.pillar.pillar if indicator.pillar else None,
                },
                'mappings': [
                    {
                        'requirement_code': m.requirement.code,
                        'requirement_title': m.requirement.title,
                        'is_primary': m.is_primary,
                        'mapping_type': m.get_mapping_type_display(),
                        'coverage_percent': m.coverage_percent,
                    }
                    for m in indicator.framework_mappings.all()
                ]
            })
        
        return result
    
    def get_total_indicators(self, obj):
        """Count total indicators."""
        return len(self.get_indicators(obj))
    
    def get_requirement_coverage(self, obj):
        """Get requirement coverage stats."""
        framework = obj.get('framework')
        if not framework:
            return None
        
        from compliance.selectors import get_framework_coverage
        return get_framework_coverage(framework)


class CreateIndicatorFrameworkMappingSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating indicator-framework mappings."""
    
    class Meta:
        model = IndicatorFrameworkMapping
        fields = [
            'indicator', 'framework', 'requirement', 'mapping_type',
            'is_primary', 'rationale', 'coverage_percent', 'is_active', 'notes'
        ]
    
    def validate(self, data):
        """Validate requirement belongs to framework."""
        framework = data.get('framework')
        requirement = data.get('requirement')
        
        if requirement and framework and requirement.framework_id != framework.id:
            raise serializers.ValidationError(
                "Requirement must belong to the specified framework"
            )
        
        return data
