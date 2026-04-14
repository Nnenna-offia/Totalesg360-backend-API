"""Compliance Gap Report Selector - aggregates compliance gaps and remediation."""
from typing import Dict, Any

from organizations.models import Organization
from compliance.models import ComplianceGapPriority, ComplianceRecommendation


def get_gap_report(organization: Organization) -> Dict[str, Any]:
    """
    Get compliance gap report with prioritized gaps and recommendations.
    
    Aggregates from Layer 5:
    - ComplianceGapPriority: identified gaps ranked by priority
    - ComplianceRecommendation: remediation recommendations
    
    Args:
        organization: Organization to report on
    
    Returns:
        Dictionary with gap report:
        {
            "organization": "TGI Ltd",
            "total_gaps": 15,
            "gaps_by_priority": {
                "critical": 3,
                "high": 5,
                "medium": 4,
                "low": 3
            },
            "gaps_by_status": {
                "open": 10,
                "in_progress": 3,
                "resolved": 2
            },
            "critical_gaps": [...],
            "recommendations": [...],
            "summary": {...}
        }
    """
    # Get all gaps for organization
    gaps_qs = ComplianceGapPriority.objects.filter(
        organization=organization
    ).select_related('requirement', 'framework').order_by('-priority_score', '-priority_level', '-created_at')
    
    # Get recommendations
    recommendations_qs = ComplianceRecommendation.objects.filter(
        organization=organization
    ).select_related('requirement').order_by('-priority')
    
    # Aggregate gaps by priority
    gaps_by_priority = {
        "high": gaps_qs.filter(priority_level="high").count(),
        "medium": gaps_qs.filter(priority_level="medium").count(),
        "low": gaps_qs.filter(priority_level="low").count(),
    }
    
    # Aggregate gaps by status - not applicable since ComplianceGapPriority doesn't have status
    gaps_by_status = {
        "active": gaps_qs.filter(is_active=True).count(),
        "inactive": gaps_qs.filter(is_active=False).count(),
    }
    
    # Get critical gaps (limit to 10)
    critical_gaps = gaps_qs.filter(
        priority_level="high"
    )[:10]
    
    return {
        "organization": organization.name,
        "organization_id": str(organization.id),
        "total_gaps": gaps_qs.count(),
        "gaps_by_priority": gaps_by_priority,
        "gaps_by_status": gaps_by_status,
        "critical_gaps": [
            {
                "requirement": gap.requirement.title if gap.requirement else "Unknown",
                "framework": gap.framework.code if gap.framework else "General",
                "gap_type": gap.gap_description,
                "priority": gap.priority_level,
                "priority_score": gap.priority_score,
                "description": gap.efforts_to_close,
                "identified_at": gap.created_at.isoformat(),
                "days_open": (
                    (gap.updated_at - gap.created_at).days 
                    if hasattr(gap, 'updated_at') else None
                ),
            }
            for gap in critical_gaps
        ],
        "recommendations": [
            {
                "requirement": rec.requirement.name if rec.requirement else "Unknown",
                "recommendation": rec.recommendation_text,
                "status": rec.status,
                "priority": rec.priority,
                "effort_level": rec.effort_level if hasattr(rec, 'effort_level') else "medium",
                "estimated_timeline": rec.estimated_timeline if hasattr(rec, 'estimated_timeline') else None,
                "assigned_to": str(rec.assigned_to_id) if hasattr(rec, 'assigned_to_id') else None,
            }
            for rec in recommendations_qs[:10]
        ],
        "summary": {
            "total_gaps": gaps_qs.count(),
            "active_gaps": gaps_by_status.get("active", 0),
            "resolution_rate": _calculate_resolution_rate(gaps_by_priority),
            "high_priority_count": gaps_by_priority.get("high", 0),
            "recommendations_pending": recommendations_qs.filter(status="pending").count(),
            "recommendations_in_progress": recommendations_qs.filter(status="in_progress").count(),
            "recommendations_completed": recommendations_qs.filter(status="completed").count(),
            "gap_priority_distribution": gaps_by_priority,
        }
    }


def _calculate_resolution_rate(gaps_by_status: Dict[str, int]) -> float:
    """Calculate gap resolution rate as percentage."""
    total = sum(gaps_by_status.values())
    if total == 0:
        return 0.0
    
    resolved = gaps_by_status.get("resolved", 0)
    return round((resolved / total) * 100, 1)


def _calculate_gap_resolution_progress(gaps_by_status: Dict[str, int]) -> str:
    """Calculate overall gap resolution progress status."""
    resolution_rate = _calculate_resolution_rate(gaps_by_status)
    
    if resolution_rate >= 80:
        return "EXCELLENT"
    elif resolution_rate >= 60:
        return "GOOD"
    elif resolution_rate >= 40:
        return "MODERATE"
    elif resolution_rate >= 20:
        return "SLOW"
    else:
        return "STALLED"
