"""Group Framework Readiness Aggregation - aggregates readiness across subsidiaries."""
from typing import Dict, Any, List, Optional
from django.db.models import Q, Avg, Count
from django.db.models.functions import Coalesce

from organizations.models import Organization
from compliance.models import FrameworkReadiness
from submissions.models import ReportingPeriod


def get_group_framework_readiness(
    parent_organization: Organization,
    reporting_period: ReportingPeriod,
) -> Dict[str, Any]:
    """
    Get aggregated framework readiness across all subsidiaries of a parent organization.
    
    Args:
        parent_organization: Parent organization
        reporting_period: Reporting period for assessment
    
    Returns:
        Dictionary with framework readiness aggregation:
        {
            "frameworks": [
                {
                    "code": "GRI",
                    "name": "Global Reporting Initiative",
                    "avg_readiness": 62,
                    "risk_level": "medium",
                    "subsidiary_count": 6,
                    "low_risk_count": 1,
                    "medium_risk_count": 3,
                    "high_risk_count": 2,
                }
            ],
            "parent_readiness": {...},  # readiness for parent itself
            "total_subsidiaries": 6,
        }
    """
    # Get all subsidiaries
    subsidiaries = Organization.objects.filter(
        parent=parent_organization
    ).values_list('id', flat=True)
    
    # Include parent as well
    org_ids = list(subsidiaries) + [parent_organization.id]
    
    # Get readiness data for all organizations and frameworks
    readiness_qs = FrameworkReadiness.objects.filter(
        organization_id__in=org_ids,
        reporting_period=reporting_period
    ).select_related('framework', 'organization')
    
    # Group by framework and aggregate
    frameworks_stats = {}
    
    for readiness in readiness_qs:
        fw = readiness.framework
        fw_code = fw.code
        
        if fw_code not in frameworks_stats:
            frameworks_stats[fw_code] = {
                'code': fw.code,
                'name': fw.name,
                'coverage_scores': [],
                'risk_levels': [],
                'orgs': [],
            }
        
        frameworks_stats[fw_code]['coverage_scores'].append(readiness.coverage_percent)
        frameworks_stats[fw_code]['risk_levels'].append(readiness.risk_level)
        frameworks_stats[fw_code]['orgs'].append({
            'id': readiness.organization.id,
            'name': readiness.organization.name,
            'coverage': readiness.coverage_percent,
            'risk_level': readiness.risk_level,
            'mandatory_coverage': readiness.mandatory_coverage_percent,
        })
    
    # Calculate aggregated readiness
    result_frameworks = []
    for fw_code, stats in frameworks_stats.items():
        avg_coverage = sum(stats['coverage_scores']) / len(stats['coverage_scores']) if stats['coverage_scores'] else 0
        
        # Determine aggregated risk level based on average coverage
        if avg_coverage >= 80:
            agg_risk = 'low'
        elif avg_coverage >= 50:
            agg_risk = 'medium'
        else:
            agg_risk = 'high'
        
        # Count risk levels
        risk_counts = {
            'low': stats['risk_levels'].count('low'),
            'medium': stats['risk_levels'].count('medium'),
            'high': stats['risk_levels'].count('high'),
        }
        
        result_frameworks.append({
            'code': stats['code'],
            'name': stats['name'],
            'avg_readiness': round(avg_coverage, 2),
            'risk_level': agg_risk,
            'subsidiary_count': len(stats['orgs']),
            'low_risk_count': risk_counts['low'],
            'medium_risk_count': risk_counts['medium'],
            'high_risk_count': risk_counts['high'],
            'subsidiaries': stats['orgs'],
        })
    
    # Get parent readiness
    parent_readiness = readiness_qs.filter(organization=parent_organization).values(
        'coverage_percent', 'mandatory_coverage_percent', 'risk_level'
    ).first()
    
    return {
        'frameworks': sorted(result_frameworks, key=lambda x: x['avg_readiness']),
        'parent_readiness': {
            'coverage': parent_readiness.get('coverage_percent', 0) if parent_readiness else None,
            'mandatory_coverage': parent_readiness.get('mandatory_coverage_percent', 0) if parent_readiness else None,
            'risk_level': parent_readiness.get('risk_level', 'high') if parent_readiness else None,
        } if parent_readiness else None,
        'total_subsidiaries': len(list(subsidiaries)),
    }


def get_group_readiness_summary(
    parent_organization: Organization,
    reporting_period: ReportingPeriod,
) -> Dict[str, Any]:
    """
    Get summary statistics for group framework readiness.
    
    Returns simple aggregation: average readiness across all subsidiaries and frameworks.
    """
    readiness_qs = FrameworkReadiness.objects.filter(
        organization__parent=parent_organization,
        reporting_period=reporting_period
    )
    
    if not readiness_qs.exists():
        return {
            'avg_readiness': None,
            'risk_level': 'unknown',
            'total_frameworks': 0,
            'total_organizations': 0,
        }
    
    avg_coverage = readiness_qs.aggregate(
        avg=Avg('coverage_percent')
    )['avg'] or 0
    
    if avg_coverage >= 80:
        risk_level = 'low'
    elif avg_coverage >= 50:
        risk_level = 'medium'
    else:
        risk_level = 'high'
    
    return {
        'avg_readiness': round(avg_coverage, 2),
        'risk_level': risk_level,
        'total_frameworks': readiness_qs.values('framework').distinct().count(),
        'total_organizations': readiness_qs.values('organization').distinct().count(),
    }
