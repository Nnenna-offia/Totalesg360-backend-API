"""ESG Summary Report Selector - aggregates ESG scores, readiness, gaps, and recommendations."""
from typing import Dict, Any, Optional

from organizations.models import Organization
from esg_scoring.models import ESGScore
from compliance.models import FrameworkReadiness, ComplianceGapPriority, ComplianceRecommendation
from submissions.models import ReportingPeriod


def get_esg_summary_report(
    organization: Organization,
    reporting_period: Optional[ReportingPeriod] = None,
) -> Dict[str, Any]:
    """
    Get ESG summary report combining scores, readiness, gaps, and recommendations.
    
    Aggregates data from:
    - Layer 6: ESGScore (environmental, social, governance scores)
    - Layer 5: FrameworkReadiness (compliance readiness)
    - Layer 5: ComplianceGapPriority (top compliance gaps)
    - Layer 5: ComplianceRecommendation (remediation recommendations)
    
    Args:
        organization: Organization to report on
        reporting_period: Optional specific reporting period. If None, uses latest.
    
    Returns:
        Dictionary with ESG summary:
        {
            "organization": "TGI Ltd",
            "reporting_period": "2026 Annual",
            "esg_score": {
                "environmental": 42.5,
                "social": 45.0,
                "governance": 40.5,
                "overall": 42.7,
                "calculation_date": "2026-04-13"
            },
            "framework_readiness": [
                {
                    "framework": "GRI",
                    "readiness_percent": 62.0,
                    "risk_level": "medium",
                    "mandatory_coverage": 75.0,
                    "optional_coverage": 50.0
                }
            ],
            "compliance_gaps": [
                {
                    "requirement": "Environmental Management System",
                    "gap_type": "missing_data",
                    "priority": "high",
                    "affected_frameworks": 3,
                    "affected_subsidiaries": 2
                }
            ],
            "recommendations": [
                {
                    "requirement": "Emission Monitoring",
                    "recommendation": "Implement quarterly emission monitoring",
                    "timeline": "3 months",
                    "effort_level": "medium",
                    "impact": "high"
                }
            ],
            "summary": {
                "total_frameworks": 5,
                "compliant_frameworks": 2,
                "critical_gaps": 3,
                "recommendations_count": 8,
                "overall_esg_rating": "MODERATE"
            }
        }
    """
    # Use latest reporting period if not specified
    if reporting_period is None:
        reporting_period = ReportingPeriod.objects.filter(
            organization=organization
        ).order_by('-end_date').first()
        
        if not reporting_period:
            return _empty_esg_summary(organization)
    
    # Get ESG score
    esg_score = ESGScore.objects.filter(
        organization=organization,
        reporting_period=reporting_period
    ).first()
    
    # Get framework readiness
    readiness_qs = FrameworkReadiness.objects.filter(
        organization=organization,
        reporting_period=reporting_period
    ).select_related('framework')
    
    # Get gaps - create querysets before slicing
    gaps_base_qs = ComplianceGapPriority.objects.filter(
        organization=organization
    ).select_related('requirement', 'framework')
    
    # Count critical gaps before slicing
    critical_gaps_count = gaps_base_qs.filter(priority_level="high").count()
    
    # Get top 5 gaps by priority (slice after other queries)
    gaps_qs = gaps_base_qs.order_by('-priority_score')[:5]
    
    # Get recommendations - count before slicing
    recommendations_base_qs = ComplianceRecommendation.objects.filter(
        organization=organization
    ).select_related('requirement')
    
    recommendations_count = recommendations_base_qs.count()
    recommendations_qs = recommendations_base_qs.order_by('-priority')[:5]
    
    return {
        "organization": organization.name,
        "organization_id": str(organization.id),
        "reporting_period": reporting_period.name if reporting_period else "N/A",
        "reporting_period_id": str(reporting_period.id) if reporting_period else None,
        "esg_score": {
            "environmental": esg_score.environmental_score if esg_score else None,
            "social": esg_score.social_score if esg_score else None,
            "governance": esg_score.governance_score if esg_score else None,
            "overall": esg_score.overall_score if esg_score else None,
            "calculation_date": esg_score.updated_at.isoformat() if esg_score else None,
        } if esg_score else None,
        "framework_readiness": [
            {
                "framework": readiness.framework.code,
                "framework_name": readiness.framework.name,
                "readiness_percent": readiness.coverage_percent,
                "readiness_score": readiness.readiness_score,
                "risk_level": readiness.risk_level,
                "mandatory_coverage": readiness.mandatory_coverage_percent,
                "total_requirements": readiness.total_requirements,
                "covered_requirements": readiness.covered_requirements,
            }
            for readiness in readiness_qs
        ],
        "compliance_gaps": [
            {
                "requirement": gap.requirement.title if gap.requirement else "Unknown",
                "framework": gap.framework.code if gap.framework else "General",
                "gap_type": gap.gap_description,
                "priority": gap.priority_level,
                "priority_score": gap.priority_score,
                "description": gap.efforts_to_close,
            }
            for gap in gaps_qs
        ],
        "recommendations": [
            {
                "requirement": rec.requirement.name if rec.requirement else "Unknown",
                "recommendation": rec.recommendation_text,
                "status": rec.status,
                "priority": rec.priority,
                "effort_level": rec.effort_level if hasattr(rec, 'effort_level') else "medium",
            }
            for rec in recommendations_qs
        ],
        "summary": {
            "total_frameworks": readiness_qs.count(),
            "medium_risk_frameworks": readiness_qs.filter(risk_level="medium").count(),
            "high_risk_frameworks": readiness_qs.filter(risk_level="high").count(),
            "critical_gaps": critical_gaps_count,
            "recommendations_count": recommendations_count,
            "overall_esg_rating": _calculate_esg_rating(esg_score) if esg_score else "UNKNOWN",
        }
    }


def _empty_esg_summary(organization: Organization) -> Dict[str, Any]:
    """Return empty ESG summary when no data available."""
    return {
        "organization": organization.name,
        "organization_id": str(organization.id),
        "reporting_period": None,
        "reporting_period_id": None,
        "esg_score": None,
        "framework_readiness": [],
        "compliance_gaps": [],
        "recommendations": [],
        "summary": {
            "total_frameworks": 0,
            "medium_risk_frameworks": 0,
            "high_risk_frameworks": 0,
            "critical_gaps": 0,
            "recommendations_count": 0,
            "overall_esg_rating": "NO_DATA",
        }
    }


def _calculate_esg_rating(esg_score: 'ESGScore') -> str:
    """Calculate ESG rating from overall score."""
    if not esg_score or not esg_score.overall_score:
        return "UNKNOWN"
    
    score = esg_score.overall_score
    if score >= 80:
        return "EXCELLENT"
    elif score >= 60:
        return "GOOD"
    elif score >= 40:
        return "MODERATE"
    elif score >= 20:
        return "WEAK"
    else:
        return "CRITICAL"
