"""Gap Priority calculation service - prioritizes compliance gaps."""
from django.db import transaction
from django.utils import timezone

from organizations.models import Organization, RegulatoryFramework
from indicators.models import Indicator
from ..models.framework_requirement import FrameworkRequirement
from ..models.compliance_gap_priority import ComplianceGapPriority
from ..selectors.framework_mapping import get_uncovered_requirements


def calculate_gap_priority(
    organization: Organization,
    framework: RegulatoryFramework,
) -> list:
    """
    Calculate priority scores for all compliance gaps.
    
    Priority Factors (total 100 points):
    - Mandatory Requirement: 40 points (if is_mandatory=True)
    - Framework Priority: 30 points (scaled from framework.priority)
    - Pillar Importance: 20 points (ENV/SOC/GOV weighting)
    - Coverage Impact: 10 points (how many indicators could satisfy this)
    
    Example Scoring:
    - Mandatory GRI 305-1 (ENV): 40 + 30 + 15 + 5 = 90 (HIGH)
    - Optional GRI 408-1 (SOC): 0 + 25 + 8 + 3 = 36 (LOW)
    
    Args:
        organization: Organization to assess
        framework: Framework to assess gaps in
    
    Returns:
        List of ComplianceGapPriority objects
    """
    
    # Get uncovered requirements
    uncovered = get_uncovered_requirements(organization, framework)
    
    pillar_weights = {
        "ENV": 15,
        "SOC": 10,
        "GOV": 5,
    }
    
    results = []
    
    for requirement in uncovered:
        # Calculate mandatory weight (40 points)
        mandatory_weight = 40.0 if requirement.is_mandatory else 0.0
        
        # Calculate framework weight (30 points, scaled by framework priority)
        # Assume framework.priority ranges from 0-10
        framework_weight = (framework.priority / 10.0) * 30.0 if framework.priority else 15.0
        
        # Calculate pillar weight (20 points)
        pillar_weight = pillar_weights.get(requirement.pillar, 5)
        
        # Calculate coverage impact weight (10 points)
        # Find indicators that could satisfy this requirement
        potential_indicators = Indicator.objects.filter(
            pillar=requirement.pillar,
            is_active=True,
        ).count()
        coverage_impact_weight = min(10.0, (potential_indicators / 5.0))  # Max 10 points
        
        # Total priority score
        priority_score = (
            mandatory_weight + framework_weight + pillar_weight + coverage_impact_weight
        )
        
        # Determine priority level
        if priority_score >= 70:
            priority_level = ComplianceGapPriority.PriorityLevel.HIGH
        elif priority_score >= 40:
            priority_level = ComplianceGapPriority.PriorityLevel.MEDIUM
        else:
            priority_level = ComplianceGapPriority.PriorityLevel.LOW
        
        # Determine impact category
        if requirement.is_mandatory:
            impact_category = ComplianceGapPriority.ImpactCategory.DIRECT
        elif requirement.pillar == "ENV":
            impact_category = ComplianceGapPriority.ImpactCategory.DIRECT
        else:
            impact_category = ComplianceGapPriority.ImpactCategory.STRATEGIC
        
        # Create or update gap priority
        gap_priority, created = ComplianceGapPriority.objects.update_or_create(
            organization=organization,
            framework=framework,
            requirement=requirement,
            defaults={
                "mandatory_weight": mandatory_weight,
                "framework_weight": framework_weight,
                "pillar_weight": pillar_weight,
                "coverage_impact_weight": coverage_impact_weight,
                "priority_score": priority_score,
                "priority_level": priority_level,
                "impact_category": impact_category,
                "gap_description": requirement.description or "",
                "is_active": True,
                "last_assessed_at": timezone.now(),
            },
        )
        
        results.append(gap_priority)
    
    return results


def calculate_all_gap_priorities(
    organization: Organization,
) -> dict:
    """
    Calculate gap priorities for all frameworks in an organization.
    
    Args:
        organization: Organization to assess
    
    Returns:
        Dictionary with results summary
    """
    org_frameworks = organization.organization_frameworks.filter(is_enabled=True)
    
    results = {}
    for org_framework in org_frameworks:
        gaps = calculate_gap_priority(organization, org_framework.framework)
        results[org_framework.framework.id] = gaps
    
    return {
        "organization_id": organization.id,
        "frameworks_processed": len(org_frameworks),
        "total_gaps": sum(len(v) for v in results.values()),
        "results": results,
    }


def get_top_priority_gaps(
    organization: Organization,
    framework: RegulatoryFramework = None,
    limit: int = 10,
) -> list:
    """
    Get top priority gaps ranked by priority score.
    
    Args:
        organization: Organization to get gaps for
        framework: Optional specific framework (if None, gets all)
        limit: Maximum number of gaps to return
    
    Returns:
        List of top priority ComplianceGapPriority objects
    """
    query = ComplianceGapPriority.objects.filter(
        organization=organization,
        is_active=True,
    ).order_by("-priority_score", "-priority_level")
    
    if framework:
        query = query.filter(framework=framework)
    
    return list(query[:limit])


def get_gap_summary_by_priority(
    organization: Organization,
) -> dict:
    """
    Get summary of gaps grouped by priority level.
    
    Args:
        organization: Organization to summarize
    
    Returns:
        Dictionary with priority breakdown
    """
    gaps = ComplianceGapPriority.objects.filter(
        organization=organization,
        is_active=True,
    )
    
    summary = {
        "high": {
            "count": 0,
            "avg_score": 0.0,
            "mandatory_count": 0,
        },
        "medium": {
            "count": 0,
            "avg_score": 0.0,
            "mandatory_count": 0,
        },
        "low": {
            "count": 0,
            "avg_score": 0.0,
            "mandatory_count": 0,
        },
    }
    
    scores_by_priority = {"high": [], "medium": [], "low": []}
    
    for gap in gaps:
        priority_key = gap.priority_level
        summary[priority_key]["count"] += 1
        scores_by_priority[priority_key].append(gap.priority_score)
        
        if gap.requirement.is_mandatory:
            summary[priority_key]["mandatory_count"] += 1
    
    # Calculate averages
    for priority in ["high", "medium", "low"]:
        if scores_by_priority[priority]:
            avg = sum(scores_by_priority[priority]) / len(scores_by_priority[priority])
            summary[priority]["avg_score"] = round(avg, 2)
    
    return summary


def deactivate_gap(
    organization: Organization,
    framework: RegulatoryFramework,
    requirement: FrameworkRequirement,
    reason: str = "",
) -> bool:
    """
    Deactivate a gap (mark as no longer needing attention).
    
    Args:
        organization: Organization with gap
        framework: Framework
        requirement: Requirement
        reason: Reason for deactivation
    
    Returns:
        True if deactivated, False if not found
    """
    try:
        gap = ComplianceGapPriority.objects.get(
            organization=organization,
            framework=framework,
            requirement=requirement,
        )
        gap.is_active = False
        gap.internal_notes = f"Deactivated: {reason}"
        gap.save(update_fields=["is_active", "internal_notes"])
        return True
    except ComplianceGapPriority.DoesNotExist:
        return False
