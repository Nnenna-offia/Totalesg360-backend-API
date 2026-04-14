"""Group Compliance Gaps Aggregation - aggregates gaps across subsidiaries."""
from typing import Dict, Any, List
from django.db.models import Q, Count
from collections import defaultdict

from organizations.models import Organization
from compliance.models import ComplianceGapPriority


def get_group_top_gaps(
    parent_organization: Organization,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Get top compliance gaps across all subsidiaries of a parent organization.
    
    Aggregates gaps by requirement and ranks by:
    1. Number of affected subsidiaries
    2. Priority level (HIGH > MEDIUM > LOW)
    
    Args:
        parent_organization: Parent organization
        limit: Maximum number of gaps to return
    
    Returns:
        List of aggregated gaps:
        [
            {
                "requirement_id": "req-123",
                "requirement_name": "Scope 1 Emissions",
                "affected_subsidiaries": 3,
                "priority": "high",
                "high_priority_count": 3,
                "medium_priority_count": 0,
                "low_priority_count": 0,
                "organizations": [
                    {
                        "org_id": "org-1",
                        "org_name": "Subsidiary A",
                        "gap_priority": "high",
                    },
                    ...
                ],
            },
            ...
        ]
    """
    # Get all subsidiaries
    subsidiaries = Organization.objects.filter(
        parent=parent_organization
    ).values_list('id', 'name')
    subsidiary_ids = [s[0] for s in subsidiaries]
    
    if not subsidiary_ids:
        return []
    
    # Get all gaps for subsidiaries
    gaps_qs = ComplianceGapPriority.objects.filter(
        organization_id__in=subsidiary_ids
    ).select_related('requirement', 'organization', 'framework').order_by('-priority_score')
    
    # Group by requirement
    gaps_by_req = defaultdict(lambda: {
        'requirement': None,
        'organizations': [],
        'priority_counts': defaultdict(int),
    })
    
    for gap in gaps_qs:
        req = gap.requirement
        req_key = f"{req.framework.code}_{req.code}"
        
        if gaps_by_req[req_key]['requirement'] is None:
            gaps_by_req[req_key]['requirement'] = req
        
        gaps_by_req[req_key]['organizations'].append({
            'org_id': str(gap.organization.id),
            'org_name': gap.organization.name,
            'gap_priority': gap.priority,
            'priority_score': gap.priority_score,
        })
        
        gaps_by_req[req_key]['priority_counts'][gap.priority] += 1
    
    # Build result list
    result = []
    for req_key, data in gaps_by_req.items():
        req = data['requirement']
        orgs = data['organizations']
        priority_counts = data['priority_counts']
        
        # Determine overall priority: if any HIGH, then HIGH; else if any MEDIUM, then MEDIUM
        overall_priority = 'low'
        if priority_counts['high'] > 0:
            overall_priority = 'high'
        elif priority_counts['medium'] > 0:
            overall_priority = 'medium'
        
        # Sort organizations by priority and score
        sorted_orgs = sorted(
            orgs,
            key=lambda x: (
                {'high': 0, 'medium': 1, 'low': 2}.get(x['gap_priority'], 3),
                -x['priority_score']
            )
        )
        
        result.append({
            'requirement_id': str(req.id),
            'requirement_code': req.code,
            'requirement_name': req.name,
            'framework_code': req.framework.code,
            'affected_subsidiaries': len(orgs),
            'priority': overall_priority,
            'high_priority_count': priority_counts['high'],
            'medium_priority_count': priority_counts['medium'],
            'low_priority_count': priority_counts['low'],
            'organizations': sorted_orgs[:5],  # Top 5 most affected
        })
    
    # Sort by affected subsidiaries and priority
    priority_map = {'high': 0, 'medium': 1, 'low': 2}
    result.sort(
        key=lambda x: (-x['affected_subsidiaries'], priority_map.get(x['priority'], 3))
    )
    
    return result[:limit]


def get_group_gap_summary(
    parent_organization: Organization,
) -> Dict[str, Any]:
    """
    Get summary statistics for group compliance gaps.
    
    Returns:
        Dictionary with gap statistics
    """
    subsidiaries = Organization.objects.filter(
        parent=parent_organization
    ).values_list('id', flat=True)
    
    if not subsidiaries:
        return {
            'total_gaps': 0,
            'high_priority_count': 0,
            'medium_priority_count': 0,
            'low_priority_count': 0,
            'most_common_gap': None,
        }
    
    gaps_qs = ComplianceGapPriority.objects.filter(
        organization_id__in=list(subsidiaries)
    )
    
    priority_counts = {
        'high': gaps_qs.filter(priority='high').count(),
        'medium': gaps_qs.filter(priority='medium').count(),
        'low': gaps_qs.filter(priority='low').count(),
    }
    
    # Most common gap
    most_common = gaps_qs.values('requirement__code').annotate(
        count=Count('id')
    ).order_by('-count').first()
    
    return {
        'total_gaps': gaps_qs.count(),
        'total_unique_requirements': gaps_qs.values('requirement').distinct().count(),
        'high_priority_count': priority_counts['high'],
        'medium_priority_count': priority_counts['medium'],
        'low_priority_count': priority_counts['low'],
        'most_common_gap_code': most_common['requirement__code'] if most_common else None,
        'most_common_gap_count': most_common['count'] if most_common else 0,
    }
