"""Group Dashboard Aggregation - unified view of group aggregated data."""
from typing import Dict, Any, Optional

from organizations.models import Organization
from submissions.models import ReportingPeriod
from .group_readiness import get_group_framework_readiness, get_group_readiness_summary
from .group_gaps import get_group_top_gaps, get_group_gap_summary
from .group_recommendations import get_group_recommendations, get_group_recommendations_summary
from .group_scoring import calculate_group_esg_score, get_subsidiary_ranking, get_group_esg_trend


def get_group_dashboard(
    parent_organization: Organization,
    reporting_period: Optional[ReportingPeriod] = None,
) -> Dict[str, Any]:
    """
    Get comprehensive group dashboard with all aggregated intelligence.
    
    Combines:
    - Group ESG Score
    - Subsidiary Ranking
    - Framework Readiness
    - Top Compliance Gaps
    - Top Recommendations
    
    Args:
        parent_organization: Parent organization
        reporting_period: Reporting period (optional)
    
    Returns:
        Comprehensive dashboard data
    """
    # Determine reporting period
    if not reporting_period:
        reporting_period = ReportingPeriod.objects.filter(
            organization=parent_organization
        ).order_by('-end_date').first()
        
        if not reporting_period:
            # Try to get from subsidiaries
            reporting_period = ReportingPeriod.objects.filter(
                organization__parent=parent_organization
            ).order_by('-end_date').first()
    
    # Get all aggregated data
    esg_score = calculate_group_esg_score(parent_organization, reporting_period) if reporting_period else None
    framework_readiness = get_group_framework_readiness(parent_organization, reporting_period) if reporting_period else None
    top_gaps = get_group_top_gaps(parent_organization, limit=5)
    top_recommendations = get_group_recommendations(parent_organization, limit=5)
    subsidiary_ranking = get_subsidiary_ranking(parent_organization, reporting_period)
    
    # Get summaries
    readiness_summary = get_group_readiness_summary(parent_organization, reporting_period) if reporting_period else None
    gap_summary = get_group_gap_summary(parent_organization)
    recommendation_summary = get_group_recommendations_summary(parent_organization)
    
    return {
        'organization': {
            'id': str(parent_organization.id),
            'name': parent_organization.name,
            'type': parent_organization.organization_type,
        },
        'reporting_period': {
            'id': str(reporting_period.id) if reporting_period else None,
            'start_date': reporting_period.start_date.isoformat() if reporting_period else None,
            'end_date': reporting_period.end_date.isoformat() if reporting_period else None,
        } if reporting_period else None,
        
        # ESG Scoring
        'esg_score': esg_score,
        'es_trend': get_group_esg_trend(parent_organization, periods=4),
        
        # Subsidiary Rankings
        'subsidiary_ranking': subsidiary_ranking,
        'total_subsidiaries': len(subsidiary_ranking),
        
        # Framework Readiness
        'framework_readiness': framework_readiness,
        'readiness_summary': readiness_summary,
        
        # Compliance Gaps
        'top_gaps': top_gaps,
        'gap_summary': gap_summary,
        
        # Recommendations
        'top_recommendations': top_recommendations,
        'recommendation_summary': recommendation_summary,
    }


def get_subsidiary_comparison(
    parent_organization: Organization,
    reporting_period: Optional[ReportingPeriod] = None,
) -> Dict[str, Any]:
    """
    Get detailed comparison view across subsidiaries.
    
    Allows side-by-side comparison of subsidiary performance.
    
    Returns:
        Comparison data with all metrics
    """
    rankings = get_subsidiary_ranking(parent_organization, reporting_period)
    
    if not rankings:
        return {
            'total_subsidiaries': 0,
            'rankings': [],
        }
    
    return {
        'total_subsidiaries': len(rankings),
        'best_performer': rankings[0] if rankings else None,
        'lowest_performer': rankings[-1] if rankings else None,
        'average_score': sum(r['overall'] for r in rankings) / len(rankings) if rankings else None,
        'rankings': rankings,
    }


def get_group_portfolio_summary(
    parent_organization: Organization,
) -> Dict[str, Any]:
    """
    Get high-level portfolio summary for investor reporting.
    
    Provides executive summary view of entire group.
    """
    # Get current period data
    dashboard = get_group_dashboard(parent_organization)
    
    return {
        'organization_name': parent_organization.name,
        'organization_id': str(parent_organization.id),
        'portfolio_size': dashboard.get('total_subsidiaries', 0),
        'overall_esg_score': dashboard.get('esg_score', {}).get('overall'),
        'environmental_score': dashboard.get('esg_score', {}).get('environmental'),
        'social_score': dashboard.get('esg_score', {}).get('social'),
        'governance_score': dashboard.get('esg_score', {}).get('governance'),
        'overall_readiness': dashboard.get('readiness_summary', {}).get('avg_readiness'),
        'compliance_gaps_count': dashboard.get('gap_summary', {}).get('total_gaps'),
        'high_priority_gaps': dashboard.get('gap_summary', {}).get('high_priority_count'),
        'pending_recommendations': dashboard.get('recommendation_summary', {}).get('pending_count'),
        'top_performing_subsidiary': dashboard.get('subsidiary_ranking', [{}])[0].get('org_name'),
        'top_performing_score': dashboard.get('subsidiary_ranking', [{}])[0].get('overall'),
    }
