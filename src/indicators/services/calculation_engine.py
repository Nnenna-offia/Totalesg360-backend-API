from __future__ import annotations

from typing import Optional, Set

from django.db import transaction
from django.db.models import Sum

from compliance.models import IndicatorFrameworkMapping
from emissions.models import EmissionFactor
from indicators.models import Indicator, IndicatorDependency, IndicatorValue


def _is_primary_indicator(indicator: Indicator) -> bool:
    return IndicatorFrameworkMapping.objects.filter(
        indicator=indicator,
        is_active=True,
        is_primary=True,
        mapping_type=IndicatorFrameworkMapping.MappingType.PRIMARY,
    ).exists()


def _get_indicator_value_sum(*, indicator: Indicator, period, org) -> float:
    agg = IndicatorValue.objects.filter(
        organization=org,
        reporting_period=period,
        indicator=indicator,
    ).aggregate(total=Sum("value"))
    return float(agg.get("total") or 0.0)


def _find_indicator_factor(*, indicator: Indicator, org, year: int) -> Optional[EmissionFactor]:
    qs = EmissionFactor.objects.filter(indicator=indicator)

    org_country = getattr(org, "country", None)
    factor = qs.filter(country=org_country, year=year).first()
    if factor:
        return factor

    factor = qs.filter(year=year).first()
    if factor:
        return factor

    return qs.filter(country__isnull=True).order_by("-year").first()


def _resolve_dependency_contribution(*, dependency: IndicatorDependency, period, org, visited: Set[str]) -> float:
    child_indicator = dependency.child_indicator
    child_value = calculate_indicator_value(
        indicator=child_indicator,
        period=period,
        org=org,
        persist=False,
        visited=visited,
    )

    multiplier = 1.0
    if dependency.relationship_type == IndicatorDependency.RelationshipType.CONVERSION:
        factor = _find_indicator_factor(indicator=child_indicator, org=org, year=period.year)
        if factor:
            multiplier = float(factor.effective_factor_value)
        elif child_indicator.emission_factor is not None:
            multiplier = float(child_indicator.emission_factor)

    weight = float(dependency.weight) if dependency.weight is not None else 1.0
    return child_value * multiplier * weight


def calculate_indicator_value(*, indicator: Indicator, period, org, persist: bool = True, visited: Optional[Set[str]] = None) -> float:
    """Calculate indicator value for an organization and period.

    Rules:
    - PRIMARY indicators: sum(child_indicator * emission_factor) using dependencies.
    - DERIVED indicators: sum child indicators using dependencies.
    - INPUT indicators: aggregate existing IndicatorValue rows.
    """
    visited = visited or set()
    node_key = str(indicator.id)
    if node_key in visited:
        return 0.0
    visited.add(node_key)

    dependencies = list(
        IndicatorDependency.objects.filter(parent_indicator=indicator, is_active=True).select_related("child_indicator")
    )

    if _is_primary_indicator(indicator):
        value = sum(
            _resolve_dependency_contribution(dependency=dep, period=period, org=org, visited=visited)
            for dep in dependencies
        )
    elif indicator.indicator_type == Indicator.IndicatorType.DERIVED:
        if dependencies:
            value = sum(
                _resolve_dependency_contribution(dependency=dep, period=period, org=org, visited=visited)
                for dep in dependencies
            )
        else:
            value = _get_indicator_value_sum(indicator=indicator, period=period, org=org)
    else:
        value = _get_indicator_value_sum(indicator=indicator, period=period, org=org)

    if persist:
        with transaction.atomic():
            IndicatorValue.objects.update_or_create(
                organization=org,
                indicator=indicator,
                reporting_period=period,
                facility=None,
                defaults={
                    "value": value,
                    "metadata": {
                        "source": "indicator_calculation_engine",
                        "computed": True,
                    },
                },
            )

    return float(value)


def recalculate_dependent_indicators(indicator: Indicator, org, period, *, _visited: Optional[Set[str]] = None) -> None:
    """Walk UP the dependency tree from *indicator* and recompute every parent.

    Called after an INPUT IndicatorValue is written so that PRIMARY / DERIVED
    aggregates are kept up-to-date automatically.

    Cycle protection is handled via *_visited* (set of indicator pk strings).
    """
    if _visited is None:
        _visited = set()

    node_key = str(indicator.id)
    if node_key in _visited:
        return
    _visited.add(node_key)

    parents = (
        IndicatorDependency.objects
        .filter(child_indicator=indicator, is_active=True)
        .select_related("parent_indicator")
    )

    for dep in parents:
        parent = dep.parent_indicator
        calculate_indicator_value(indicator=parent, period=period, org=org, persist=True)
        # Recurse so higher-level aggregates (e.g. Total Emissions) are also refreshed
        recalculate_dependent_indicators(parent, org, period, _visited=_visited)


def get_affected_indicators(indicator: Indicator) -> Set[Indicator]:
    """Return *indicator* plus every ancestor reachable via IndicatorDependency.

    Example chain: Diesel → Scope 1 → Total Emissions
    Calling this with Diesel returns {Diesel, Scope 1, Total Emissions}.

    Optimized to avoid per-node queries by loading active dependencies once and
    traversing an in-memory parent adjacency map.
    """
    dependency_rows = IndicatorDependency.objects.filter(is_active=True).values_list(
        "child_indicator_id",
        "parent_indicator_id",
    )
    parent_map = {}
    for child_id, parent_id in dependency_rows:
        parent_map.setdefault(str(child_id), []).append(str(parent_id))

    visited_ids: Set[str] = set()
    result_ids: Set[str] = set()

    def _dfs(current_id: str) -> None:
        if current_id in visited_ids:
            return
        visited_ids.add(current_id)
        result_ids.add(current_id)
        for parent_id in parent_map.get(current_id, []):
            _dfs(parent_id)

    _dfs(str(indicator.id))
    return set(Indicator.objects.filter(id__in=result_ids))
