"""Group ESG Score Aggregation - aggregates ESG scores across subsidiaries."""
from typing import Dict, Any, List, Optional
from django.db.models import Q, Avg, Count
from decimal import Decimal

from organizations.models import Organization
from esg_scoring.models import ESGScore
from submissions.models import ReportingPeriod


def calculate_group_esg_score(
    parent_organization: Organization,
    reporting_period: ReportingPeriod,
    use_weighted_average: bool = False,
) -> Dict[str, Any]:
    """
    Calculate group ESG score by aggregating subsidiary scores.
    
    Supports:
    - Simple average across all subsidiaries
    - Weighted average (by revenue, employee count, or other factors)
    
    Args:
        parent_organization: Parent organization
        reporting_period: Reporting period for calculation
        use_weighted_average: Whether to use weighted aggregation
    
    Returns:
        Dictionary with aggregated group ESG score:
        {
            "environmental": 39,
            "social": 45,
            "governance": 42,
            "overall": 42,
            "subsidiary_count": 6,
            "calculation_method": "simple_average" or "weighted_average",
            "subsidiaries": [
                {
                    "org_id": "org-1",
                    "org_name": "Subsidiary A",
                    "environmental": 40,
                    "social": 45,
                    "governance": 38,
                    "overall": 41,
                    "weight": 0.2,  # if weighted_average
                },
                ...
            ],
        }
    """
    # Get all subsidiaries
    subsidiaries = Organization.objects.filter(
        parent=parent_organization
    ).select_related('parent').values_list('id', 'name')
    subsidiary_ids = [s[0] for s in subsidiaries]
    
    if not subsidiary_ids:
        return {
            'environmental': None,
            'social': None,
            'governance': None,
            'overall': None,
            'subsidiary_count': 0,
            'calculation_method': 'simple_average',
            'subsidiaries': [],
        }
    
    # Get ESG scores for all subsidiaries
    scores_qs = ESGScore.objects.filter(
        organization_id__in=subsidiary_ids,
        reporting_period=reporting_period,
        is_consolidated=False  # Get individual org scores, not already consolidated
    ).select_related('organization')
    
    if not scores_qs.exists():
        return {
            'environmental': None,
            'social': None,
            'governance': None,
            'overall': None,
            'subsidiary_count': len(subsidiary_ids),
            'calculation_method': 'simple_average',
            'subsidiaries': [],
        }
    
    # Build subsidiary scores
    subsidiary_scores = []
    env_scores = []
    soc_scores = []
    gov_scores = []
    overall_scores = []
    
    weights = []
    
    for score in scores_qs:
        weight = _calculate_subsidiary_weight(score.organization) if use_weighted_average else 1.0
        weights.append(weight)
        
        env_scores.append(score.environmental_score * weight)
        soc_scores.append(score.social_score * weight)
        gov_scores.append(score.governance_score * weight)
        overall_scores.append(score.overall_score * weight)
        
        subsidiary_scores.append({
            'org_id': str(score.organization.id),
            'org_name': score.organization.name,
            'environmental': round(score.environmental_score, 2),
            'social': round(score.social_score, 2),
            'governance': round(score.governance_score, 2),
            'overall': round(score.overall_score, 2),
            'weight': round(weight, 4) if use_weighted_average else None,
        })
    
    # Calculate aggregated scores
    total_weight = sum(weights)
    
    env_avg = sum(env_scores) / total_weight if total_weight > 0 else 0
    soc_avg = sum(soc_scores) / total_weight if total_weight > 0 else 0
    gov_avg = sum(gov_scores) / total_weight if total_weight > 0 else 0
    overall_avg = sum(overall_scores) / total_weight if total_weight > 0 else 0
    
    return {
        'environmental': round(env_avg, 2),
        'social': round(soc_avg, 2),
        'governance': round(gov_avg, 2),
        'overall': round(overall_avg, 2),
        'subsidiary_count': scores_qs.count(),
        'calculation_method': 'weighted_average' if use_weighted_average else 'simple_average',
        'subsidiaries': subsidiary_scores,
    }


def get_subsidiary_ranking(
    parent_organization: Organization,
    reporting_period: Optional[ReportingPeriod] = None,
) -> List[Dict[str, Any]]:
    """
    Rank subsidiaries by ESG score.
    
    Args:
        parent_organization: Parent organization
        reporting_period: Optional reporting period (uses latest if not specified)
    
    Returns:
        List of subsidiaries ranked by ESG score:
        [
            {
                "rank": 1,
                "org_id": "org-1",
                "org_name": "Titan Trust",
                "environmental": 50,
                "social": 60,
                "governance": 55,
                "overall": 55,
                "organization_type": "subsidiary",
            },
            ...
        ]
    """
    subsidiaries = Organization.objects.filter(
        parent=parent_organization,
        entity_type=Organization.EntityType.SUBSIDIARY,
    ).values_list('id', 'name', 'entity_type')
    subsidiary_ids = [s[0] for s in subsidiaries]
    
    if not subsidiary_ids:
        return []
    
    filters = Q(organization_id__in=subsidiary_ids, is_consolidated=False)
    
    if reporting_period:
        filters &= Q(reporting_period=reporting_period)
    
    # Get latest reporting period if not specified
    elif not reporting_period:
        latest_period = ReportingPeriod.objects.filter(
            organization__parent=parent_organization
        ).order_by('-end_date').first()
        if latest_period:
            filters &= Q(reporting_period=latest_period)
    
    scores_qs = ESGScore.objects.filter(filters).select_related('organization')
    
    if not scores_qs.exists():
        return []
    
    # Build ranking
    ranking = []
    for idx, score in enumerate(scores_qs.order_by('-overall_score'), 1):
        ranking.append({
            'rank': idx,
            'org_id': str(score.organization.id),
            'org_name': score.organization.name,
            'environmental': round(score.environmental_score, 2),
            'social': round(score.social_score, 2),
            'governance': round(score.governance_score, 2),
            'overall': round(score.overall_score, 2),
            'organization_type': score.organization.organization_type,
            'change': None,  # Future: track score changes over periods
        })
    
    return ranking


def get_group_esg_trend(
    parent_organization: Organization,
    periods: int = 4,
) -> List[Dict[str, Any]]:
    """
    Get ESG score trends for group over multiple reporting periods.
    
    Args:
        parent_organization: Parent organization
        periods: Number of periods to include
    
    Returns:
        List of score trends over time
    """
    subsidiaries = Organization.objects.filter(
        parent=parent_organization
    ).values_list('id', flat=True)
    
    if not subsidiaries:
        return []
    
    # Get available reporting periods
    periods_qs = ReportingPeriod.objects.filter(
        organization__parent=parent_organization
    ).distinct().order_by('-end_date')[:periods]
    
    trends = []
    for period in reversed(periods_qs):
        group_score = calculate_group_esg_score(parent_organization, period)
        
        trends.append({
            'period': str(period.id),
            'period_name': f"{period.start_date.strftime('%Y-%m-%d')} to {period.end_date.strftime('%Y-%m-%d')}",
            'end_date': period.end_date.isoformat(),
            'environmental': group_score.get('environmental'),
            'social': group_score.get('social'),
            'governance': group_score.get('governance'),
            'overall': group_score.get('overall'),
        })
    
    return trends


def _calculate_subsidiary_weight(organization: Organization) -> float:
    """
    Calculate weight for subsidiary in aggregation.
    
    Future enhancement: use employee_count, revenue, or other metrics.
    For now, all subsidiaries have equal weight.
    """
    # TODO: Implement weighted calculation based on:
    # - organization.employee_count
    # - organization.revenue
    # - organization.facility_size
    return 1.0
