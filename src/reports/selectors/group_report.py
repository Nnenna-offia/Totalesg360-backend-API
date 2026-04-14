"""Group ESG Report Selector - aggregates group-level ESG data from Layer 7."""
from typing import Dict, Any

from organizations.models import Organization
from submissions.models import ReportingPeriod

# Import Layer 7 selectors
from group_analytics.selectors import (
    get_group_dashboard,
    get_subsidiary_ranking,
    calculate_group_esg_score,
)


def get_group_esg_report(
    parent_organization: Organization,
    reporting_period: ReportingPeriod = None,
) -> Dict[str, Any]:
    """
    Get group-level ESG report using Layer 7 aggregation.
    
    Reuses:
    - Layer 7: Group dashboard (comprehensive metrics)
    - Layer 7: Subsidiary ranking (ESG scores by subsidiary)
    - Layer 7: Group ESG score (weighted/simple average)
    
    Args:
        parent_organization: Parent organization
        reporting_period: Optional reporting period
    
    Returns:
        Dictionary with group ESG report:
        {
            "organization": "TGI Group",
            "organization_type": "group",
            "reporting_period": "2026 Annual",
            "esg_score": {
                "environmental": 42.5,
                "social": 45.0,
                "governance": 40.5,
                "overall": 42.7,
                "subsidiary_count": 6
            },
            "subsidiaries": [
                {
                    "rank": 1,
                    "name": "TGI Ltd",
                    "environmental": 50.0,
                    "social": 52.0,
                    "governance": 48.0,
                    "overall": 50.0
                }
            ],
            "summary": {...}
        }
    """
    if parent_organization.organization_type != Organization.OrganizationType.GROUP:
        return _empty_group_report(parent_organization, "Not a group organization")
    
    # Get group dashboard (all metrics combined)
    dashboard = get_group_dashboard(parent_organization, reporting_period)
    
    # Get subsidiary ranking
    ranking = get_subsidiary_ranking(parent_organization, reporting_period)
    
    # Get aggregate ESG score
    esg_score = calculate_group_esg_score(parent_organization, reporting_period)
    
    # Count subsidiaries
    subsidiary_count = parent_organization.children.count()
    
    return {
        "organization": parent_organization.name,
        "organization_id": str(parent_organization.id),
        "organization_type": parent_organization.get_organization_type_display(),
        "reporting_period": reporting_period.name if reporting_period else "Latest",
        "reporting_period_id": str(reporting_period.id) if reporting_period else None,
        "esg_score": {
            "environmental": esg_score.get('environmental'),
            "social": esg_score.get('social'),
            "governance": esg_score.get('governance'),
            "overall": esg_score.get('overall'),
            "calculation_method": esg_score.get('calculation_method'),
            "subsidiary_count": esg_score.get('subsidiary_count'),
        },
        "subsidiaries": [
            {
                "rank": sub.get('rank'),
                "organization_id": sub.get('org_id'),
                "name": sub.get('org_name'),
                "environmental": sub.get('environmental'),
                "social": sub.get('social'),
                "governance": sub.get('governance'),
                "overall": sub.get('overall'),
                "organization_type": sub.get('organization_type'),
            }
            for sub in (ranking.get('ranking') or [])
        ],
        "dashboard_metrics": dashboard if dashboard else {},
        "summary": {
            "total_subsidiaries": subsidiary_count,
            "reporting_coverage": esg_score.get('subsidiary_count', 0),
            "reporting_coverage_percent": (
                (esg_score.get('subsidiary_count', 0) / subsidiary_count * 100)
                if subsidiary_count > 0 else 0
            ),
            "top_performing_subsidiary": (
                ranking.get('ranking')[0]['org_name'] 
                if ranking.get('ranking') else None
            ),
            "bottom_performing_subsidiary": (
                ranking.get('ranking')[-1]['org_name'] 
                if ranking.get('ranking') else None
            ),
        }
    }


def _empty_group_report(organization: Organization, reason: str = "") -> Dict[str, Any]:
    """Return empty group report."""
    return {
        "organization": organization.name,
        "organization_id": str(organization.id),
        "organization_type": organization.get_organization_type_display(),
        "reporting_period": None,
        "reporting_period_id": None,
        "error": f"Cannot generate group report: {reason}",
        "esg_score": None,
        "subsidiaries": [],
        "dashboard_metrics": {},
        "summary": {
            "total_subsidiaries": 0,
            "reporting_coverage": 0,
            "reporting_coverage_percent": 0,
        }
    }
