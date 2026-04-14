"""Framework Readiness calculation service - calculates compliance readiness scores."""
from django.db import transaction
from django.utils import timezone

from organizations.models import Organization, RegulatoryFramework
from submissions.models import ReportingPeriod
from ..models.framework_readiness import FrameworkReadiness
from ..selectors.framework_mapping import (
    get_framework_requirements,
    get_framework_coverage,
)


def calculate_framework_readiness(
    organization: Organization,
    framework: RegulatoryFramework,
    reporting_period: ReportingPeriod,
) -> FrameworkReadiness:
    """
    Calculate framework readiness for an organization.
    
    Readiness Score = (Mandatory Coverage * 0.7) + (Optional Coverage * 0.3)
    
    Risk Levels:
    - Low: Readiness >= 80%
    - Medium: Readiness >= 50% and < 80%
    - High: Readiness < 50%
    
    Args:
        organization: Organization being assessed
        framework: Framework to assess against
        reporting_period: Reporting period for assessment
    
    Returns:
        FrameworkReadiness object with calculated scores
    
    Example:
        >>> org = Organization.objects.first()
        >>> framework = RegulatoryFramework.objects.get(code="GRI")
        >>> period = ReportingPeriod.objects.first()
        >>> readiness = calculate_framework_readiness(org, framework, period)
        >>> print(f"Readiness: {readiness.readiness_score}%")
        >>> print(f"Risk: {readiness.risk_level}")
    """
    
    # Get framework coverage data
    coverage_data = get_framework_coverage(organization, framework)
    
    # Extract coverage metrics
    total_reqs = coverage_data.get("total_requirements", 0)
    covered_reqs = coverage_data.get("covered_requirements", 0)
    mandatory_total = coverage_data.get("mandatory_requirements", 0)
    mandatory_covered = coverage_data.get("mandatory_covered", 0)
    
    # Calculate coverage percentages
    coverage_percent = (covered_reqs / total_reqs * 100) if total_reqs > 0 else 0.0
    mandatory_coverage_percent = (
        (mandatory_covered / mandatory_total * 100) if mandatory_total > 0 else 0.0
    )
    
    # Calculate optional coverage
    optional_total = total_reqs - mandatory_total
    optional_covered = covered_reqs - mandatory_covered
    optional_coverage_percent = (
        (optional_covered / optional_total * 100) if optional_total > 0 else 0.0
    )
    
    # Calculate readiness score (weighted average)
    # Mandatory requirements are 70% of the score, optional are 30%
    readiness_score = (mandatory_coverage_percent * 0.7) + (optional_coverage_percent * 0.3)
    
    # Determine risk level
    if readiness_score >= 80:
        risk_level = FrameworkReadiness.RiskLevel.LOW
    elif readiness_score >= 50:
        risk_level = FrameworkReadiness.RiskLevel.MEDIUM
    else:
        risk_level = FrameworkReadiness.RiskLevel.HIGH
    
    # Create or update readiness record
    readiness, created = FrameworkReadiness.objects.update_or_create(
        organization=organization,
        framework=framework,
        reporting_period=reporting_period,
        defaults={
            "total_requirements": total_reqs,
            "covered_requirements": covered_reqs,
            "coverage_percent": max(0.0, min(100.0, coverage_percent)),
            "mandatory_requirements": mandatory_total,
            "mandatory_covered": mandatory_covered,
            "mandatory_coverage_percent": max(0.0, min(100.0, mandatory_coverage_percent)),
            "readiness_score": max(0.0, min(100.0, readiness_score)),
            "risk_level": risk_level,
            "is_current": True,
            "calculated_at": timezone.now(),
        },
    )
    
    return readiness


def calculate_all_framework_readiness(
    organization: Organization,
    reporting_period: ReportingPeriod,
) -> list:
    """
    Calculate readiness for all enabled frameworks for an organization.
    
    Args:
        organization: Organization to assess
        reporting_period: Reporting period for assessment
    
    Returns:
        List of FrameworkReadiness objects
    """
    # Get all enabled frameworks for organization
    org_frameworks = organization.organization_frameworks.filter(is_enabled=True)
    
    results = []
    for org_framework in org_frameworks:
        readiness = calculate_framework_readiness(
            organization=organization,
            framework=org_framework.framework,
            reporting_period=reporting_period,
        )
        results.append(readiness)
    
    return results


def batch_calculate_framework_readiness(
    reporting_period: ReportingPeriod,
) -> dict:
    """
    Calculate readiness for all organizations for a given period.
    
    Args:
        reporting_period: Reporting period to calculate for
    
    Returns:
        Dictionary with results summary
    """
    from organizations.models import Organization
    
    organizations = Organization.objects.filter(is_active=True)
    
    results = {}
    for org in organizations:
        results[org.id] = calculate_all_framework_readiness(org, reporting_period)
    
    return {
        "organizations_processed": len(organizations),
        "total_readiness_scores": sum(len(v) for v in results.values()),
        "results": results,
    }


@transaction.atomic
def mark_readiness_as_current(
    organization: Organization,
    framework: RegulatoryFramework = None,
) -> int:
    """
    Mark readiness assessments as current (used when updating older records).
    
    Args:
        organization: Organization to update
        framework: Optional specific framework (if None, updates all)
    
    Returns:
        Number of records marked as current
    """
    query = FrameworkReadiness.objects.filter(organization=organization)
    
    if framework:
        query = query.filter(framework=framework)
    
    updated_count, _ = query.update(is_current=True, calculated_at=timezone.now())
    
    return updated_count


def get_readiness_summary_by_risk(
    organization: Organization,
) -> dict:
    """
    Get summary of framework readiness grouped by risk level.
    
    Args:
        organization: Organization to summarize
    
    Returns:
        Dictionary with risk level breakdown
    
    Example Output:
        {
            "low": {
                "count": 5,
                "frameworks": [...]
            },
            "medium": {
                "count": 3,
                "frameworks": [...]
            },
            "high": {
                "count": 2,
                "frameworks": [...]
            }
        }
    """
    readiness_scores = FrameworkReadiness.objects.filter(
        organization=organization,
        is_current=True,
    )
    
    summary = {
        "low": {
            "count": 0,
            "frameworks": [],
            "avg_readiness": 0.0,
        },
        "medium": {
            "count": 0,
            "frameworks": [],
            "avg_readiness": 0.0,
        },
        "high": {
            "count": 0,
            "frameworks": [],
            "avg_readiness": 0.0,
        },
    }
    
    readiness_by_risk = {
        "low": [],
        "medium": [],
        "high": [],
    }
    
    for readiness in readiness_scores:
        risk_key = readiness.risk_level
        readiness_by_risk[risk_key].append(readiness.readiness_score)
        
        summary[risk_key]["count"] += 1
        summary[risk_key]["frameworks"].append({
            "code": readiness.framework.code,
            "name": readiness.framework.name,
            "readiness": readiness.readiness_score,
            "coverage": readiness.coverage_percent,
        })
    
    # Calculate averages
    for risk_level in ["low", "medium", "high"]:
        if readiness_by_risk[risk_level]:
            avg = sum(readiness_by_risk[risk_level]) / len(readiness_by_risk[risk_level])
            summary[risk_level]["avg_readiness"] = round(avg, 2)
    
    return summary
