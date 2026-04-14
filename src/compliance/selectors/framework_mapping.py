"""Selectors for framework and indicator mappings."""
from django.db.models import Count, Q, Prefetch, F, Value, CharField, Case, When
from django.db.models.functions import Concat
from organizations.models import Organization, RegulatoryFramework, OrganizationFramework
from indicators.models import Indicator
from ..models import FrameworkRequirement, IndicatorFrameworkMapping


def get_organization_frameworks(organization):
    """
    Get all frameworks associated with an organization.
    
    Returns:
        QuerySet of OrganizationFramework objects with prefetched requirements
    
    Example:
        frameworks = get_organization_frameworks(org)
        for org_fw in frameworks:
            print(f"{org_fw.framework.name} - Primary: {org_fw.is_primary}")
    """
    return (
        OrganizationFramework.objects
        .filter(organization=organization, is_enabled=True)
        .select_related("framework")
        .prefetch_related(
            Prefetch(
                "framework__requirements",
                queryset=FrameworkRequirement.objects.filter(status=FrameworkRequirement.Status.ACTIVE)
            )
        )
        .order_by("-is_primary", "-framework__priority")
    )


def get_framework_indicators(framework):
    """
    Get all indicators mapped to a framework.
    
    Returns:
        QuerySet of Indicators with their mappings to this framework
    
    Example:
        gri_indicators = get_framework_indicators(gri_framework)
        for indicator, mappings in gri_indicators.items():
            print(f"{indicator}: {len(mappings)} mappings")
    """
    return (
        Indicator.objects
        .filter(
            regulatory_requirement_mappings__framework=framework,
            regulatory_requirement_mappings__is_active=True
        )
        .distinct()
        .select_related("category", "pillar")
        .prefetch_related(
            Prefetch(
                "regulatory_requirement_mappings",
                queryset=IndicatorFrameworkMapping.objects.filter(
                    framework=framework,
                    is_active=True
                ).select_related("requirement").order_by("-is_primary")
            )
        )
        .annotate(mapping_count=Count("regulatory_requirement_mappings", distinct=True))
        .order_by("-mapping_count", "category__name")
    )


def get_indicator_frameworks(indicator):
    """
    Get all frameworks that an indicator is mapped to.
    
    Includes requirement details and mapping rationale.
    
    Returns:
        List of dicts with framework and requirement mapping info
    
    Example:
        frameworks = get_indicator_frameworks(scope1_emissions)
        for fw in frameworks:
            print(f"{fw['framework'].name}: {fw['requirement'].code}")
    """
    mappings = (
        IndicatorFrameworkMapping.objects
        .filter(indicator=indicator, is_active=True)
        .select_related("framework", "requirement")
        .order_by("framework__priority", "requirement__pillar")
    )
    
    result = []
    for mapping in mappings:
        result.append({
            "indicator": indicator,
            "framework": mapping.framework,
            "requirement": mapping.requirement,
            "mapping": mapping,
            "mapping_type": mapping.get_mapping_type_display(),
            "coverage_status": mapping.get_coverage_status(),
        })
    
    return result


def get_framework_requirements(framework):
    """
    Get all requirements for a framework with coverage info.
    
    Returns:
        QuerySet of FrameworkRequirement with indicator coverage counts
    
    Example:
        requirements = get_framework_requirements(gri_framework)
        for req in requirements:
            print(f"{req.code}: {req.indicator_count} indicators")
    """
    return (
        FrameworkRequirement.objects
        .filter(framework=framework, status=FrameworkRequirement.Status.ACTIVE)
        .annotate(
            covered_by_count=Count(
                "indicator_mappings",
                filter=Q(indicator_mappings__is_active=True)
            ),
            primary_indicator_count=Count(
                "indicator_mappings",
                filter=Q(indicator_mappings__is_primary=True, indicator_mappings__is_active=True)
            )
        )
        .order_by("pillar", "priority", "code")
    )


def get_framework_coverage(framework):
    """
    Get overall coverage statistics for a framework.
    
    Returns:
        Dict with coverage metrics
    
    Example:
        coverage = get_framework_coverage(gri_framework)
        print(f"Coverage: {coverage['total_requirements']} requirements")
        print(f"Covered: {coverage['covered_requirements']} ({coverage['coverage_percent']}%)")
    """
    requirements = get_framework_requirements(framework)
    
    total = requirements.count()
    covered = sum(1 for r in requirements if r.covered_by_count > 0)
    uncovered = total - covered
    
    coverage_by_pillar = {}
    for pillar_choice in FrameworkRequirement.Pillar.choices:
        pillar = pillar_choice[0]
        pillar_reqs = requirements.filter(pillar=pillar)
        pillar_total = pillar_reqs.count()
        pillar_covered = sum(1 for r in pillar_reqs if r.covered_by_count > 0)
        
        coverage_by_pillar[pillar] = {
            "total": pillar_total,
            "covered": pillar_covered,
            "uncovered": pillar_total - pillar_covered,
            "coverage_percent": (pillar_covered / pillar_total * 100) if pillar_total > 0 else 0,
        }
    
    return {
        "framework": framework,
        "total_requirements": total,
        "covered_requirements": covered,
        "uncovered_requirements": uncovered,
        "coverage_percent": (covered / total * 100) if total > 0 else 0,
        "by_pillar": coverage_by_pillar,
    }


def get_uncovered_requirements(organization, framework):
    """
    Find requirements not yet covered by organization's indicators.
    
    Used for gap analysis and compliance planning.
    
    Returns:
        QuerySet of uncovered FrameworkRequirement objects
    
    Example:
        gaps = get_uncovered_requirements(tgi_org, gri_framework)
        for req in gaps:
            print(f"Missing: {req.code} - {req.title}")
    """
    # Get all active indicators for the organization
    org_indicators = Indicator.objects.filter(
        organization=organization,
        is_active=True
    )
    
    # Find requirements that have no mappings to these indicators
    return (
        FrameworkRequirement.objects
        .filter(framework=framework, status=FrameworkRequirement.Status.ACTIVE)
        .exclude(
            indicator_mappings__indicator__in=org_indicators,
            indicator_mappings__is_active=True
        )
        .distinct()
        .order_by("pillar", "priority", "code")
    )


def get_organization_framework_status(organization):
    """
    Get compliance status across all frameworks for an organization.
    
    Returns:
        List of framework coverage dicts
    
    Example:
        status = get_organization_framework_status(tgi_org)
        for fw_status in status:
            print(f"{fw_status['framework'].name}: {fw_status['coverage_percent']}%")
    """
    org_frameworks = get_organization_frameworks(organization)
    
    result = []
    for org_fw in org_frameworks:
        coverage = get_framework_coverage(org_fw.framework)
        result.append({
            "organization_framework": org_fw,
            "framework": org_fw.framework,
            **coverage,
            "is_primary": org_fw.is_primary,
        })
    
    return sorted(result, key=lambda x: (-x["is_primary"], -x["coverage_percent"]))


def get_indicator_requirement_gaps(indicator, framework):
    """
    Find requirements related to indicator's pillar that aren't covered.
    
    Returns:
        QuerySet of uncovered FrameworkRequirement objects for same pillar
    """
    return (
        FrameworkRequirement.objects
        .filter(
            framework=framework,
            pillar=indicator.pillar.pillar,  # Same pillar
            status=FrameworkRequirement.Status.ACTIVE
        )
        .exclude(
            indicator_mappings__indicator=indicator,
            indicator_mappings__is_active=True
        )
        .distinct()
        .order_by("priority", "code")
    )
