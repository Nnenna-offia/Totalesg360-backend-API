"""Group Recommendations Aggregation - aggregates recommendations across subsidiaries."""
from typing import Dict, Any, List
from django.db.models import Count
from collections import defaultdict

from organizations.models import Organization
from compliance.models import ComplianceRecommendation


def get_group_recommendations(
    parent_organization: Organization,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Get aggregated recommendations across all subsidiaries of a parent organization.
    
    Groups recommendations by requirement and ranks by:
    1. Number of affected subsidiaries
    2. Priority level (HIGH > MEDIUM > LOW)
    
    Args:
        parent_organization: Parent organization
        limit: Maximum number of recommendations to return
    
    Returns:
        List of aggregated recommendations:
        [
            {
                "recommendation_id": "rec-123",
                "title": "Implement Scope 1 emissions tracking",
                "recommendation_type": "create_indicator",
                "affected_subsidiaries": 3,
                "priority": "high",
                "high_priority_count": 3,
                "medium_priority_count": 0,
                "low_priority_count": 0,
                "in_progress_count": 1,
                "completed_count": 0,
                "organizations": [
                    {
                        "org_id": "org-1",
                        "org_name": "Subsidiary A",
                        "status": "pending",
                        "priority": "high",
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
    
    # Get all recommendations for subsidiaries (pending and in_progress only)
    recs_qs = ComplianceRecommendation.objects.filter(
        organization_id__in=subsidiary_ids,
    ).exclude(
        status=ComplianceRecommendation.Status.COMPLETED
    ).select_related('requirement', 'organization', 'framework')
    
    # Group by requirement and title
    recs_by_key = defaultdict(lambda: {
        'recommendation': None,
        'organizations': [],
        'priority_counts': defaultdict(int),
        'status_counts': defaultdict(int),
    })
    
    for rec in recs_qs:
        req = rec.requirement
        rec_key = f"{rec.title}_{rec.recommendation_type}_{req.code}"
        
        if recs_by_key[rec_key]['recommendation'] is None:
            recs_by_key[rec_key]['recommendation'] = rec
        
        recs_by_key[rec_key]['organizations'].append({
            'org_id': str(rec.organization.id),
            'org_name': rec.organization.name,
            'status': rec.status,
            'priority': rec.priority,
        })
        
        recs_by_key[rec_key]['priority_counts'][rec.priority] += 1
        recs_by_key[rec_key]['status_counts'][rec.status] += 1
    
    # Build result list
    result = []
    for rec_key, data in recs_by_key.items():
        rec = data['recommendation']
        orgs = data['organizations']
        priority_counts = data['priority_counts']
        status_counts = data['status_counts']
        
        # Determine overall priority
        overall_priority = 'low'
        if priority_counts['high'] > 0:
            overall_priority = 'high'
        elif priority_counts['medium'] > 0:
            overall_priority = 'medium'
        
        # Sort organizations
        sorted_orgs = sorted(
            orgs,
            key=lambda x: (
                {'high': 0, 'medium': 1, 'low': 2}.get(x['priority'], 3),
            )
        )
        
        result.append({
            'recommendation_id': str(rec.id),
            'title': rec.title,
            'description': rec.description,
            'recommendation_type': rec.recommendation_type,
            'framework_code': rec.framework.code,
            'affected_subsidiaries': len(orgs),
            'priority': overall_priority,
            'high_priority_count': priority_counts['high'],
            'medium_priority_count': priority_counts['medium'],
            'low_priority_count': priority_counts['low'],
            'pending_count': status_counts[ComplianceRecommendation.Status.PENDING],
            'in_progress_count': status_counts[ComplianceRecommendation.Status.IN_PROGRESS],
            'deferred_count': status_counts[ComplianceRecommendation.Status.DEFERRED],
            'organizations': sorted_orgs[:5],  # Top 5 affected
        })
    
    # Sort by affected subsidiaries and priority
    priority_map = {'high': 0, 'medium': 1, 'low': 2}
    result.sort(
        key=lambda x: (-x['affected_subsidiaries'], priority_map.get(x['priority'], 3))
    )
    
    return result[:limit]


def get_group_recommendations_summary(
    parent_organization: Organization,
) -> Dict[str, Any]:
    """
    Get summary statistics for group recommendations.
    
    Returns:
        Dictionary with recommendation statistics
    """
    subsidiaries = Organization.objects.filter(
        parent=parent_organization
    ).values_list('id', flat=True)
    
    if not subsidiaries:
        return {
            'total_recommendations': 0,
            'high_priority_count': 0,
            'medium_priority_count': 0,
            'low_priority_count': 0,
            'pending_count': 0,
            'in_progress_count': 0,
            'completed_count': 0,
        }
    
    recs_qs = ComplianceRecommendation.objects.filter(
        organization_id__in=list(subsidiaries)
    )
    
    return {
        'total_recommendations': recs_qs.count(),
        'high_priority_count': recs_qs.filter(priority='high').count(),
        'medium_priority_count': recs_qs.filter(priority='medium').count(),
        'low_priority_count': recs_qs.filter(priority='low').count(),
        'pending_count': recs_qs.filter(status=ComplianceRecommendation.Status.PENDING).count(),
        'in_progress_count': recs_qs.filter(status=ComplianceRecommendation.Status.IN_PROGRESS).count(),
        'completed_count': recs_qs.filter(status=ComplianceRecommendation.Status.COMPLETED).count(),
        'deferred_count': recs_qs.filter(status=ComplianceRecommendation.Status.DEFERRED).count(),
    }
