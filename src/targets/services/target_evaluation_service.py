"""Service to evaluate a TargetGoal and persist a TargetEvaluation snapshot."""
from decimal import Decimal
from typing import Optional

from targets.models import TargetGoal, TargetEvaluation
from targets.selectors.target_selectors import get_indicator_current_value
from submissions.models import ReportingPeriod


def evaluate_and_save_target(
    goal: TargetGoal,
    reporting_period: ReportingPeriod,
) -> TargetEvaluation:
    """Calculate current performance for *goal* in *reporting_period* and persist it.

    Always returns a TargetEvaluation — status is set to NO_DATA when no
    IndicatorValue exists yet so that the system behaves correctly before
    the first data submission arrives.
    """
    actual = get_indicator_current_value(
        goal.indicator,
        goal.organization,
        period=reporting_period,
    )
    if actual is None:
        return TargetEvaluation.objects.create(
            target=goal,
            reporting_period=reporting_period,
            actual_value=0.0,
            variance=0.0,
            progress_percent=0,
            status=TargetEvaluation.Status.NO_DATA,
        )

    actual_d = Decimal(str(actual))
    target_d = Decimal(str(goal.target_value))
    baseline_d = Decimal(str(goal.baseline_value))

    variance = float(actual_d - target_d)

    # progress percent (same formula as calculate_target_progress)
    if baseline_d == target_d:
        pct = 100 if actual_d == target_d else 0
    else:
        if goal.direction == TargetGoal.Direction.DECREASE:
            denom = baseline_d - target_d
            num = baseline_d - actual_d
        else:
            denom = target_d - baseline_d
            num = actual_d - baseline_d
        try:
            pct = int((num / denom) * 100) if denom != 0 else 0
        except Exception:
            pct = 0
    pct = max(0, min(100, pct))

    # status
    if pct >= 100:
        status = TargetEvaluation.Status.ACHIEVED
    elif goal.direction == TargetGoal.Direction.DECREASE:
        status = TargetEvaluation.Status.ON_TRACK if actual <= goal.target_value else TargetEvaluation.Status.BEHIND
    else:
        status = TargetEvaluation.Status.ON_TRACK if actual >= goal.target_value else TargetEvaluation.Status.BEHIND

    return TargetEvaluation.objects.create(
        target=goal,
        reporting_period=reporting_period,
        actual_value=float(actual_d),
        variance=variance,
        progress_percent=pct,
        status=status,
    )


def evaluate_targets_for_indicator(
    indicator,
    organization,
    reporting_period: ReportingPeriod,
) -> int:
    """Evaluate only the active targets that reference *indicator* for *organization*.

    More efficient than evaluate_all_targets_for_period when a single
    IndicatorValue changes — avoids re-evaluating unrelated targets.

    Returns the number of evaluations created.
    """
    goals = TargetGoal.objects.filter(
        organization=organization,
        indicator=indicator,
        status=TargetGoal.Status.ACTIVE,
    )

    count = 0
    for goal in goals:
        evaluate_and_save_target(goal, reporting_period)
        count += 1
    return count


def evaluate_all_targets_for_period(
    organization,
    reporting_period: ReportingPeriod,
) -> int:
    """Evaluate all active targets for *organization* in *reporting_period*.

    Returns the number of evaluations created.
    """
    goals = TargetGoal.objects.filter(
        organization=organization,
        status=TargetGoal.Status.ACTIVE,
    ).select_related("indicator")

    count = 0
    for goal in goals:
        evaluate_and_save_target(goal, reporting_period)
        count += 1
    return count
