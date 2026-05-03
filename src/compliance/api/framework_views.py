"""API views for framework mapping and compliance requirements."""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from common.permissions import IsOrgMember, HasGlobalCapability
from organizations.models import RegulatoryFramework, OrganizationFramework
from indicators.models import Indicator
from compliance.models import FrameworkRequirement, IndicatorFrameworkMapping
from compliance.selectors import (
    get_framework_requirements,
    get_framework_indicators,
    get_indicator_frameworks,
    get_framework_coverage,
    get_uncovered_requirements,
    get_organization_frameworks,
    get_organization_framework_status,
)
from .serializers import (
    RegulatoryFrameworkSerializer,
    FrameworkRequirementSerializer,
    FrameworkRequirementDetailSerializer,
    IndicatorFrameworkMappingSerializer,
    IndicatorFrameworkMappingDetailSerializer,
    CreateIndicatorFrameworkMappingSerializer,
    FrameworkCoverageSerializer,
    OrganizationFrameworkStatusSerializer,
    IndicatorFrameworksSerializer,
    FrameworkIndicatorsSerializer,
)


class FrameworkRequirementViewSet(viewsets.ModelViewSet):
    """ViewSet for framework requirements."""
    
    queryset = FrameworkRequirement.objects.filter(status=FrameworkRequirement.Status.ACTIVE)
    required_capability = 'framework.manage'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['framework', 'pillar', 'is_mandatory']
    search_fields = ['code', 'title', 'description']
    ordering_fields = ['pillar', 'priority', 'code']
    ordering = ['pillar', 'priority', 'code']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return FrameworkRequirementDetailSerializer
        return FrameworkRequirementSerializer

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [AllowAny()]
        return [IsAuthenticated(), HasGlobalCapability()]
    
    @action(detail=False, methods=['get'])
    def by_framework(self, request):
        """Get requirements for a specific framework.
        
        Query params:
            - framework_id: UUID of framework (required)
        """
        framework_id = request.query_params.get('framework_id')
        if not framework_id:
            return Response(
                {'error': 'framework_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        framework = get_object_or_404(RegulatoryFramework, id=framework_id)
        requirements = get_framework_requirements(framework)
        
        serializer = FrameworkRequirementDetailSerializer(requirements, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def coverage(self, request):
        """Get coverage statistics for a framework.
        
        Query params:
            - framework_id: UUID of framework (required)
        """
        framework_id = request.query_params.get('framework_id')
        if not framework_id:
            return Response(
                {'error': 'framework_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        framework = get_object_or_404(RegulatoryFramework, id=framework_id)
        coverage = get_framework_coverage(framework)
        
        serializer = FrameworkCoverageSerializer(coverage)
        return Response(serializer.data)


class IndicatorFrameworkMappingViewSet(viewsets.ModelViewSet):
    """ViewSet for Indicator-Framework mappings."""
    
    queryset = IndicatorFrameworkMapping.objects.filter(is_active=True)
    required_capability = 'framework.manage'
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['indicator', 'framework', 'is_primary', 'mapping_type']
    ordering_fields = ['-is_primary', '-coverage_percent', 'framework__code']
    ordering = ['-is_primary', '-coverage_percent']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CreateIndicatorFrameworkMappingSerializer
        elif self.action == 'retrieve':
            return IndicatorFrameworkMappingDetailSerializer
        return IndicatorFrameworkMappingSerializer

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [AllowAny()]
        return [IsAuthenticated(), HasGlobalCapability()]
    
    @action(detail=False, methods=['get'])
    def for_indicator(self, request):
        """Get all framework mappings for an indicator.
        
        Query params:
            - indicator_id: UUID of indicator (required)
        """
        indicator_id = request.query_params.get('indicator_id')
        if not indicator_id:
            return Response(
                {'error': 'indicator_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        indicator = get_object_or_404(Indicator, id=indicator_id)
        frameworks = get_indicator_frameworks(indicator)
        
        # Return structured response
        framework_list = {}
        for item in frameworks:
            fw_code = item['framework'].code
            if fw_code not in framework_list:
                framework_list[fw_code] = {
                    'framework': RegulatoryFrameworkSerializer(item['framework']).data,
                    'requirements': []
                }
            
            framework_list[fw_code]['requirements'].append({
                'code': item['requirement'].code,
                'title': item['requirement'].title,
                'mapping_type': item['mapping_type'],
                'coverage_status': item['coverage_status'],
                'is_primary': item['mapping'].is_primary,
                'coverage_percent': item['mapping'].get_dynamic_coverage_percent(),
            })
        
        return Response({
            'indicator': {
                'id': str(indicator.id),
                'code': indicator.code,
                'name': indicator.name,
            },
            'frameworks': list(framework_list.values()),
            'total_frameworks': len(framework_list),
        })
    
    @action(detail=False, methods=['get'])
    def for_framework(self, request):
        """Get all indicator mappings for a framework.
        
        Query params:
            - framework_id: UUID of framework (required)
        """
        framework_id = request.query_params.get('framework_id')
        if not framework_id:
            return Response(
                {'error': 'framework_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        framework = get_object_or_404(RegulatoryFramework, id=framework_id)
        indicators = get_framework_indicators(framework)
        
        # Build response
        indicator_list = []
        for indicator in indicators:
            indicator_list.append({
                'indicator': {
                    'id': str(indicator.id),
                    'code': indicator.code,
                    'name': indicator.name,
                    'pillar': indicator.pillar.pillar if indicator.pillar else None,
                },
                'mappings': IndicatorFrameworkMappingSerializer(
                    indicator.regulatory_requirement_mappings.filter(framework=framework, is_active=True),
                    many=True
                ).data,
            })
        
        return Response({
            'framework': RegulatoryFrameworkSerializer(framework).data,
            'indicators': indicator_list,
            'total_indicators': len(indicator_list),
        })
    
    @action(detail=False, methods=['get'])
    def gaps(self, request):
        """Get uncovered requirements for an organization in a framework.
        
        Query params:
            - organization_id: UUID of organization (required)
            - framework_id: UUID of framework (required)
        """
        org_id = request.query_params.get('organization_id')
        framework_id = request.query_params.get('framework_id')
        
        if not org_id or not framework_id:
            return Response(
                {'error': 'organization_id and framework_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from organizations.models import Organization
        org = get_object_or_404(Organization, id=org_id)
        framework = get_object_or_404(RegulatoryFramework, id=framework_id)
        
        gaps = get_uncovered_requirements(org, framework)
        
        # Group by pillar
        gaps_by_pillar = {}
        for gap in gaps:
            pillar = gap.pillar
            if pillar not in gaps_by_pillar:
                gaps_by_pillar[pillar] = []
            gaps_by_pillar[pillar].append(FrameworkRequirementDetailSerializer(gap).data)
        
        return Response({
            'organization': {'id': str(org.id), 'name': org.name},
            'framework': RegulatoryFrameworkSerializer(framework).data,
            'gaps': gaps_by_pillar,
            'total_gaps': gaps.count(),
        })


class OrganizationFrameworkViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for organization's framework assignments."""
    
    permission_classes = [IsOrgMember]
    serializer_class = RegulatoryFrameworkSerializer
    
    def get_queryset(self):
        org = getattr(self.request, 'organization', None)
        if not org:
            return RegulatoryFramework.objects.none()
        
        org_frameworks = OrganizationFramework.objects.filter(
            organization=org,
            is_enabled=True
        ).values_list('framework_id', flat=True)
        
        return RegulatoryFramework.objects.filter(id__in=org_frameworks)
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """Get compliance status across all assigned frameworks."""
        org = getattr(request, 'organization', None)
        if not org:
            return Response(
                {'error': 'Organization context not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        status_data = get_organization_framework_status(org)
        serializer = OrganizationFrameworkStatusSerializer(status_data, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def all(self, request):
        """Get all configured frameworks for the organization."""
        org = getattr(request, 'organization', None)
        if not org:
            return Response(
                {'error': 'Organization context not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        org_frameworks = get_organization_frameworks(org)
        
        result = []
        for org_fw in org_frameworks:
            coverage = get_framework_coverage(org_fw.framework)
            result.append({
                'organization_framework': {
                    'id': str(org_fw.id),
                    'is_primary': org_fw.is_primary,
                    'is_enabled': org_fw.is_enabled,
                    'assigned_at': org_fw.assigned_at,
                },
                'framework': RegulatoryFrameworkSerializer(org_fw.framework).data,
                'coverage': FrameworkCoverageSerializer(coverage).data,
            })
        
        return Response(result)


class FrameworkListViewSet(viewsets.ModelViewSet):
    """ViewSet for global framework listing and editing."""
    
    queryset = RegulatoryFramework.objects.all().order_by('-priority', 'name')
    serializer_class = RegulatoryFrameworkSerializer
    required_capability = 'framework.manage'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['jurisdiction', 'sector', 'is_active', 'is_system']
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['priority', 'name']
    ordering = ['-priority', 'name']

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [AllowAny()]
        return [IsAuthenticated(), HasGlobalCapability()]
