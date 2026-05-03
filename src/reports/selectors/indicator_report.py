"""Indicator Report Selector — actual vs target per indicator for a reporting period."""
from typing import Any, Dict, List, Optional

from django.db.models import Sum

from indicators.models import IndicatorValue
from indicators.selectors.queries import get_org_effective_indicators
from organizations.models import Organization
from submissions.models import ReportingPeriod
from targets.models import TargetGoal


def _get_actual_value(org: Organization, indicator, period: ReportingPeriod) -> Optional[float]:
    """Sum all IndicatorValue rows for this org/indicator/period (across facilities)."""
    total = (
        IndicatorValue.objects.filter(
            organization=org,
            indicator=indicator,
            reporting_period=period,
        )
        .aggregate(total=Sum("value"))
        .get("total")
    )
    return float(total) if total is not None else None


def _get_active_target(org: Organization, indicator) -> Optional[TargetGoal]:
    """Return the single active TargetGoal for this org+indicator, or None."""
    return (
        TargetGoal.objects.filter(
            organization=org,
            indicator=indicator,
            status=TargetGoal.Status.ACTIVE,
        )
        .order_by("-created_at")
        .first()
    )


def get_indicator_report(
    org: Organization,
    period: ReportingPeriod,
) -> List[Dict[str, Any]]:
    """Return per-indicator actual vs target report for the given org and period.

    Each row contains:
    - indicator code / name / pillar / unit
    - actual   — current IndicatorValue sum (None if no data)
    - target   — TargetGoal.target_value (None if no goal)
    - variance — actual - target (None if either is missing)
    - status   — "on_track" | "behind" | "no_target" | "no_data"
    """
    indicators = get_org_effective_indicators(org)

    result: List[Dict[str, Any]] = []

    for indicator in indicators:
        actual = _get_actual_value(org, indicator, period)
        target_goal = _get_active_target(org, indicator)

        if target_goal is None:
            variance = None
            status = "no_target"
        elif actual is None:
            variance = None
            status = "no_data"
        else:
            variance = round(actual - target_goal.target_value, 6)
            if target_goal.direction == TargetGoal.Direction.DECREASE:
                status = "on_track" if actual <= target_goal.target_value else "behind"
            else:
                status = "on_track" if actual >= target_goal.target_value else "behind"

        result.append(
            {
                "indicator_id": str(indicator.id),
                "indicator_code": indicator.code,
                "indicator_name": indicator.name,
                "pillar": indicator.pillar,
                "unit": indicator.unit or "",
                "actual": actual,
                "target": target_goal.target_value if target_goal else None,
                "target_direction": target_goal.direction if target_goal else None,
                "variance": variance,
                "status": status,
            }
        )

    return result
