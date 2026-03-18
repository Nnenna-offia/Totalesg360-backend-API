from typing import List
from django.db.models import OuterRef, Subquery, Exists, Case, When, Value, BooleanField, F

from indicators.models import Indicator, FrameworkIndicator, OrganizationIndicator
from organizations.models import OrganizationFramework


def get_framework_indicators(framework) -> List[FrameworkIndicator]:
    """Return FrameworkIndicator rows for a framework ordered by display_order."""
    return FrameworkIndicator.objects.filter(framework=framework).select_related('indicator').order_by('display_order')


def get_org_effective_indicators(org):
    """Return Indicator queryset annotated with effective flags for the organization.

    Annotations:
      - is_required_effective: boolean
      - is_active_effective: boolean
      - overridden: boolean (True if org has an explicit OrganizationIndicator)
    """
    # enabled frameworks for org
    enabled_fws = OrganizationFramework.objects.filter(organization=org, is_enabled=True).values('framework')

    # Subquery: org override is_required
    org_override_qs = OrganizationIndicator.objects.filter(organization=org, indicator=OuterRef('pk'))

    override_required = Subquery(org_override_qs.values('is_required')[:1])
    override_active = Subquery(org_override_qs.values('is_active')[:1])
    override_exists = Exists(org_override_qs)

    # Exists: any enabled framework marks this indicator required
    required_by_framework = Exists(
        FrameworkIndicator.objects.filter(framework__in=enabled_fws, indicator=OuterRef('pk'), is_required=True)
    )

    qs = (
        Indicator.objects.all()
        .annotate(
            override_required=override_required,
            override_active=override_active,
            overridden=Case(When(override_required__isnull=False, then=Value(True)), default=Value(False), output_field=BooleanField()),
            required_by_framework=required_by_framework,
        )
    )

    # compute effective flags in Python-friendly annotation via Case
    qs = qs.annotate(
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

    return qs


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
