from typing import List
from django.db.models import OuterRef, Subquery, Exists, Case, When, Value, BooleanField, F

from indicators.models import Indicator, OrganizationIndicator
from compliance.models import IndicatorFrameworkMapping
from organizations.models import OrganizationFramework
from organizations.selectors.frameworks import get_active_frameworks


def get_framework_indicators(framework):
    """Return indicators for a framework with mapping metadata, ordered by requirement priority.
    
    Derives display_order from requirement sequence and mapping type.
    Returns: QuerySet of IndicatorFrameworkMapping objects with indicator and requirement.
    """
    return (
        IndicatorFrameworkMapping.objects
        .filter(requirement__framework=framework, is_active=True)
        .select_related('indicator', 'requirement')
        .order_by('requirement__priority', 'requirement__code')
    )


def get_org_effective_indicators(org):
    """Return Indicator queryset annotated with effective flags for the organization.

    Annotations:
      - is_required_effective: boolean
      - is_active_effective: boolean
      - overridden: boolean (True if org has an explicit OrganizationIndicator)
    """
    enabled_fws = get_active_frameworks(org).values('id')

    # Subquery: org override is_required
    org_override_qs = OrganizationIndicator.objects.filter(organization=org, indicator=OuterRef('pk'))

    override_required = Subquery(org_override_qs.values('is_required')[:1])
    override_active = Subquery(org_override_qs.values('is_active')[:1])
    override_exists = Exists(org_override_qs)

    # Exists: any enabled framework has a mandatory requirement for this indicator
    required_by_framework = Exists(
        IndicatorFrameworkMapping.objects.filter(
            requirement__framework__in=enabled_fws,
            indicator=OuterRef('pk'),
            requirement__is_mandatory=True,
            is_active=True
        )
    )

    qs = (
        Indicator.objects.filter(
            is_active=True,
            regulatory_requirement_mappings__requirement__framework__in=enabled_fws,
            regulatory_requirement_mappings__is_active=True,
        )
        .distinct()
        .annotate(
            override_required=override_required,
            override_active=override_active,
            override_exists=override_exists,
            required_by_framework=required_by_framework,
        )
    )

    # compute effective flags in Python-friendly annotation via Case
    qs = qs.annotate(
        overridden=Case(
            When(override_exists=True, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        ),
        is_required_effective=Case(
            When(override_required__isnull=False, then=F('override_required')),
            When(required_by_framework=True, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        ),
        is_active_effective=Case(
            When(override_active__isnull=False, then=F('override_active')),
            default=Value(True),
            output_field=BooleanField(),
        ),
    )

    try:
        settings = org.esg_settings
    except Exception:
        settings = None

    if settings:
        if not settings.enable_environmental:
            qs = qs.exclude(pillar="ENV")
        if not settings.enable_social:
            qs = qs.exclude(pillar="SOC")
        if not settings.enable_governance:
            qs = qs.exclude(pillar="GOV")

    return qs


def get_active_indicators(org):
    return get_org_effective_indicators(org).filter(is_active_effective=True).distinct()


def get_indicator_emission_value(indicator_code: str, org=None, reporting_period=None):
    """Return emission-derived value for specific indicator codes.

    Supported codes (convention):
      - total_scope1_emissions
      - total_scope2_emissions
      - total_scope3_emissions
      - total_emissions

    Returns a numeric total (0 if none).
    """
    if reporting_period is None or org is None:
        return 0

    # Lazy import to avoid circular imports at module load
    from emissions.selectors.queries import (
        get_scope1_emissions,
        get_scope2_emissions,
        get_scope3_emissions,
        get_total_emissions,
    )

    code = (indicator_code or '').lower().strip()
    if code == 'total_scope1_emissions':
        return get_scope1_emissions(org, reporting_period)
    if code == 'total_scope2_emissions':
        return get_scope2_emissions(org, reporting_period)
    if code == 'total_scope3_emissions':
        return get_scope3_emissions(org, reporting_period)
    if code in ('total_emissions', 'total_scope_emissions'):
        return get_total_emissions(org, reporting_period)

    # Unknown indicator code: default to 0
    return 0
