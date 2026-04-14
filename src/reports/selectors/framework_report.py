"""Framework Report Selector - detailed framework compliance report."""
from typing import Dict, Any

from organizations.models import Organization, RegulatoryFramework
from compliance.models import FrameworkReadiness, ComplianceGapPriority, ComplianceRecommendation


def get_framework_report(
    organization: Organization,
    framework: RegulatoryFramework,
    reporting_period_id: str = None,
) -> Dict[str, Any]:
    """
    Get detailed compliance framework report.
    
    Aggregates:
    - FrameworkReadiness: coverage %, risk levels
    - ComplianceGapPriority: gaps specific to framework
    - ComplianceRecommendation: recommendations to close gaps
    
    Args:
        organization: Organization to report on
        framework: Regulatory framework to report on
        reporting_period_id: Optional reporting period UUID
    
    Returns:
        Dictionary with framework report:
        {
            "framework": "GRI",
            "framework_name": "Global Reporting Initiative",
            "organization": "TGI Ltd",
            "readiness": {
                "coverage_percent": 62.0,
                "risk_level": "medium",
                "mandatory_coverage": 75.0,
                "optional_coverage": 50.0,
                "total_requirements": 100,
                "covered_requirements": 62
            },
            "gaps": [...],
            "recommendations": [...],
            "summary": {...}
        }
    """
    # Get readiness for this framework
    readiness = FrameworkReadiness.objects.filter(
        organization=organization,
        framework=framework
    ).order_by('-created_at').first()
    
    # Get gaps specific to this framework
    gaps_base_qs = ComplianceGapPriority.objects.filter(
        organization=organization,
        framework=framework
    ).select_related('requirement')
    
    # Count critical gaps before using queryset
    critical_gaps_count = gaps_base_qs.filter(priority_level="high").count()
    
    gaps_qs = gaps_base_qs.order_by('-priority_score')
    
    # Get recommendations for this framework (not gap-specific)
    recommendations_qs = ComplianceRecommendation.objects.filter(
        organization=organization,
        framework=framework
    ).select_related('requirement').order_by('-priority')
    
    return {
        "framework": framework.code,
        "framework_name": framework.name,
        "framework_jurisdiction": framework.get_jurisdiction_display(),
        "organization": organization.name,
        "organization_id": str(organization.id),
        "readiness": {
            "coverage_percent": readiness.coverage_percent if readiness else 0.0,
            "readiness_score": readiness.readiness_score if readiness else 0.0,
            "risk_level": readiness.risk_level if readiness else "high",
            "mandatory_coverage": readiness.mandatory_coverage_percent if readiness else 0.0,
            "total_requirements": readiness.total_requirements if readiness else 0,
            "covered_requirements": readiness.covered_requirements if readiness else 0,
            "assessment_date": readiness.updated_at.isoformat() if readiness else None,
        },
        "gaps": [
            {
                "requirement": gap.requirement.title if gap.requirement else "Unknown",
                "gap_type": gap.gap_description,
                "priority": gap.priority_level,
                "priority_score": gap.priority_score,
                "description": gap.efforts_to_close,
                "identified_at": gap.created_at.isoformat(),
            }
            for gap in gaps_qs
        ],
        "recommendations": [
            {
                "requirement": rec.requirement.title if rec.requirement else "Unknown",
                "recommendation": rec.recommendation_text,
                "status": rec.status,
                "priority": rec.priority,
                "effort_level": rec.effort_level if hasattr(rec, 'effort_level') else "medium",
                "estimated_timeline": rec.estimated_timeline if hasattr(rec, 'estimated_timeline') else None,
            }
            for rec in recommendations_qs
        ],
        "summary": {
            "total_gaps": gaps_qs.count(),
            "critical_gaps": critical_gaps_count,
            "active_gaps": gaps_qs.filter(is_active=True).count(),
            "recommendations_count": recommendations_qs.count(),
            "compliance_status": _get_compliance_status(readiness) if readiness else "UNKNOWN",
        }
    }


def _get_compliance_status(readiness: FrameworkReadiness) -> str:
    """Determine compliance status from readiness score."""
    if not readiness:
        return "UNKNOWN"
    
    score = readiness.readiness_score
    if score >= 80:
        return "COMPLIANT"
    elif score >= 60:
        return "SUBSTANTIALLY_COMPLIANT"
    elif score >= 40:
        return "PARTIALLY_COMPLIANT"
    else:
        return "NON_COMPLIANT"
