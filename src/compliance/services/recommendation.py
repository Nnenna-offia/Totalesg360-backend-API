"""Recommendation generation service - creates actionable compliance recommendations."""
from django.db import transaction
from django.utils import timezone

from organizations.models import Organization, RegulatoryFramework
from ..models.compliance_recommendation import ComplianceRecommendation
from ..models.compliance_gap_priority import ComplianceGapPriority
from ..selectors.framework_mapping import get_uncovered_requirements


def generate_recommendations(
    organization: Organization,
    framework: RegulatoryFramework,
) -> list:
    """
    Generate recommendations to close compliance gaps.
    
    For each uncovered requirement, generate actionable steps based on:
    1. Requirement type (indicator, process, governance)
    2. Organization context
    3. Industry best practices
    
    Args:
        organization: Organization to generate recommendations for
        framework: Framework to generate recommendations for
    
    Returns:
        List of ComplianceRecommendation objects
    """
    
    # Get prioritized gaps
    gaps = ComplianceGapPriority.objects.filter(
        organization=organization,
        framework=framework,
        is_active=True,
    ).order_by("-priority_score")
    
    results = []
    
    for gap in gaps:
        requirement = gap.requirement
        
        # Determine recommendation type based on pillar and requirement
        rec_type = _determine_recommendation_type(requirement)
        
        # Generate title and description
        title, description = _generate_recommendation_text(requirement, organization)
        
        # Generate actionable steps
        steps = _generate_action_steps(requirement, rec_type)
        
        # Calculate impact score (0-10)
        impact_score = _calculate_impact_score(requirement, gap)
        
        # Map priority
        priority = gap.priority_level
        
        # Estimate effort
        effort_days = _estimate_effort(rec_type)
        
        # Dependencies
        dependencies = _find_dependencies(requirement, framework)
        
        # Create or update recommendation
        recommendation, created = ComplianceRecommendation.objects.update_or_create(
            organization=organization,
            framework=framework,
            requirement=requirement,
            recommendation_type=rec_type,
            defaults={
                "title": title,
                "description": description,
                "actionable_steps": steps,
                "impact_score": impact_score,
                "priority": priority,
                "estimated_effort_days": effort_days,
                "dependencies": dependencies,
                "status": ComplianceRecommendation.Status.PENDING,
            },
        )
        
        results.append(recommendation)
    
    return results


def _determine_recommendation_type(requirement) -> str:
    """Determine recommendation type based on requirement."""
    code = requirement.code.lower()
    
    # Specific patterns
    if "emission" in code or "ghg" in code or "energy" in code:
        return ComplianceRecommendation.RecommendationType.CREATE_INDICATOR
    elif "train" in code or "develop" in code or "skill" in code:
        return ComplianceRecommendation.RecommendationType.TRAINING_REQUIRED
    elif "board" in code or "governance" in code or "oversight" in code:
        return ComplianceRecommendation.RecommendationType.GOVERNANCE_UPDATE
    elif "data" in code or "disclosure" in code:
        return ComplianceRecommendation.RecommendationType.ENHANCE_DATA
    elif "system" in code or "integration" in code:
        return ComplianceRecommendation.RecommendationType.INTEGRATE_SYSTEM
    else:
        return ComplianceRecommendation.RecommendationType.IMPLEMENT_PROCESS


def _generate_recommendation_text(requirement, organization: Organization) -> tuple:
    """Generate title and description for recommendation."""
    
    title = f"Implement {requirement.code}: {requirement.title}"
    
    description = f"""Address compliance requirement {requirement.code} from {requirement.framework.name}.

{requirement.description}

Status: {'Mandatory' if requirement.is_mandatory else 'Recommended'}
Pillar: {requirement.get_pillar_display()}

This requirement is currently uncovered by {organization.name}'s ESG data collection.
"""
    
    return title, description


def _generate_action_steps(requirement, rec_type: str) -> list:
    """Generate specific action steps for recommendation."""
    
    steps = []
    
    if rec_type == ComplianceRecommendation.RecommendationType.CREATE_INDICATOR:
        steps = [
            "1. Define indicator metrics and data collection method",
            "2. Select collection technology (activity-based, direct submission, etc.)",
            "3. Set up data validation rules and quality checks",
            "4. Configure reporting period calculation",
            "5. Train data collectors on submission process",
            "6. Enable indicator in system",
        ]
    
    elif rec_type == ComplianceRecommendation.RecommendationType.ENHANCE_DATA:
        steps = [
            "1. Audit current data sources",
            "2. Identify missing data elements",
            "3. Establish data collection procedures",
            "4. Implement verification process",
            "5. Document data lineage",
            "6. Enable data submission",
        ]
    
    elif rec_type == ComplianceRecommendation.RecommendationType.INTEGRATE_SYSTEM:
        steps = [
            "1. Identify system to integrate with",
            "2. Define data mapping requirements",
            "3. Configure API/data connector",
            "4. Test data flow",
            "5. Validate data quality",
            "6. Go live with integration",
        ]
    
    elif rec_type == ComplianceRecommendation.RecommendationType.TRAINING_REQUIRED:
        steps = [
            "1. Identify training needs",
            "2. Design training program",
            "3. Schedule training sessions",
            "4. Deliver training",
            "5. Assess competency",
            "6. Document completion",
        ]
    
    elif rec_type == ComplianceRecommendation.RecommendationType.GOVERNANCE_UPDATE:
        steps = [
            "1. Review governance structure",
            "2. Identify governance gaps",
            "3. Update policies/procedures",
            "4. Present to board/committee",
            "5. Approve changes",
            "6. Communicate to organization",
        ]
    
    else:
        steps = [
            "1. Define process requirements",
            "2. Document procedure",
            "3. Assign responsibility",
            "4. Schedule implementation",
            "5. Train staff",
            "6. Monitor execution",
        ]
    
    return steps


def _calculate_impact_score(requirement, gap: "ComplianceGapPriority") -> float:
    """Calculate expected impact on readiness score (0-10)."""
    
    # Base impact on mandatory requirement
    base_impact = 7.0 if requirement.is_mandatory else 3.0
    
    # Boost for high priority gaps
    if gap.priority_level == "high":
        base_impact += 2.0
    elif gap.priority_level == "medium":
        base_impact += 1.0
    
    # Max 10, min 1
    return min(10.0, max(1.0, base_impact))


def _estimate_effort(rec_type: str) -> int:
    """Estimate implementation effort in days."""
    
    estimates = {
        ComplianceRecommendation.RecommendationType.CREATE_INDICATOR: 5,
        ComplianceRecommendation.RecommendationType.ENHANCE_DATA: 3,
        ComplianceRecommendation.RecommendationType.INTEGRATE_SYSTEM: 10,
        ComplianceRecommendation.RecommendationType.TRAINING_REQUIRED: 2,
        ComplianceRecommendation.RecommendationType.GOVERNANCE_UPDATE: 7,
        ComplianceRecommendation.RecommendationType.IMPLEMENT_PROCESS: 4,
    }
    
    return estimates.get(rec_type, 5)


def _find_dependencies(requirement, framework: RegulatoryFramework) -> list:
    """Find other requirements that might be dependencies."""
    
    # In a real system, this would analyze requirement relationships
    # For now, return empty list
    return []


def get_recommendations_by_priority(
    organization: Organization,
    priority: str = None,
) -> list:
    """
    Get recommendations filtered by priority.
    
    Args:
        organization: Organization
        priority: "high", "medium", or "low" (None = all)
    
    Returns:
        List of recommendations
    """
    query = ComplianceRecommendation.objects.filter(
        organization=organization,
        status=ComplianceRecommendation.Status.PENDING,
    ).order_by("-priority", "-impact_score")
    
    if priority:
        query = query.filter(priority=priority)
    
    return list(query)


def get_recommendations_summary(organization: Organization) -> dict:
    """
    Get summary of recommendations by priority and status.
    
    Args:
        organization: Organization
    
    Returns:
        Dictionary with recommendation breakdown
    """
    recommendations = ComplianceRecommendation.objects.filter(
        organization=organization,
    )
    
    summary = {
        "total": recommendations.count(),
        "by_priority": {
            "high": recommendations.filter(priority="high").count(),
            "medium": recommendations.filter(priority="medium").count(),
            "low": recommendations.filter(priority="low").count(),
        },
        "by_status": {
            "pending": recommendations.filter(status="pending").count(),
            "in_progress": recommendations.filter(status="in_progress").count(),
            "completed": recommendations.filter(status="completed").count(),
            "deferred": recommendations.filter(status="deferred").count(),
        },
        "high_impact_pending": recommendations.filter(
            is_active=True,
            priority="high",
            status="pending",
        ).count(),
        "avg_effort_days": _calculate_average_effort(recommendations.filter(status="pending")),
    }
    
    return summary


def _calculate_average_effort(queryset) -> float:
    """Calculate average effort for recommendations."""
    if not queryset.exists():
        return 0.0
    
    total_effort = sum(r.estimated_effort_days for r in queryset)
    return round(total_effort / queryset.count(), 1)


@transaction.atomic
def mark_recommendation_completed(
    organization: Organization,
    framework: RegulatoryFramework,
    requirement,
    rec_type: str,
) -> bool:
    """
    Mark recommendation as completed.
    
    Args:
        organization: Organization
        framework: Framework
        requirement: Requirement
        rec_type: Recommendation type
    
    Returns:
        True if marked completed, False if not found
    """
    try:
        rec = ComplianceRecommendation.objects.get(
            organization=organization,
            framework=framework,
            requirement=requirement,
            recommendation_type=rec_type,
        )
        rec.mark_completed()
        return True
    except ComplianceRecommendation.DoesNotExist:
        return False
