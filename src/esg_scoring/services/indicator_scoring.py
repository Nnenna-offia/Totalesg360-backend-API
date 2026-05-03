"""Indicator Scoring Service - calculates scores for individual indicators."""
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
import logging

from organizations.models import Organization
from indicators.models import Indicator
from indicators.models import IndicatorValue
from submissions.models import ReportingPeriod
from targets.models import TargetGoal
from esg_scoring.models import IndicatorScore

logger = logging.getLogger(__name__)


@transaction.atomic
def calculate_indicator_score(
    organization: Organization,
    indicator: Indicator,
    reporting_period: ReportingPeriod
) -> IndicatorScore:
    """
    Calculate score for a single indicator in an organization.

    Logic:
    1. Get all submissions for this indicator in this period
    2. Get target goal for this indicator
    3. Aggregate submission values
    4. Compare actual vs target
    5. Calculate score and status
    6. Store result

    Args:
        organization: Organization being scored
        indicator: Indicator to score
        reporting_period: Reporting period

    Returns:
        IndicatorScore object
    """

    try:
        # IndicatorValue is the single source of truth for scored values.
        indicator_values = IndicatorValue.objects.filter(
            organization=organization,
            indicator=indicator,
            reporting_period=reporting_period,
        )

        if not indicator_values.exists():
            logger.warning(
                f"No indicator values for {indicator.name} in {organization.name}"
            )
            # Score 0 if no values exist yet.
            return _create_or_update_indicator_score(
                organization=organization,
                indicator=indicator,
                reporting_period=reporting_period,
                score=0,
                value=None,
                baseline=0,
                target=0,
                progress=0,
                status=IndicatorScore.ScoreStatus.POOR,
                calculation_method="no_indicator_value",
            )

        total_value = float(indicator_values.aggregate(total=Sum("value")).get("total") or 0)

        # Get target goal
        target_goal = TargetGoal.objects.filter(
            organization=organization,
            indicator=indicator,
            status=TargetGoal.Status.ACTIVE,
        ).first()

        if not target_goal:
            logger.warning(f"No target goal found for {indicator.name}")
            baseline = 0
            target = 0
            score = 0
            progress = 0
            status = IndicatorScore.ScoreStatus.POOR
        else:
            baseline = target_goal.baseline_value or 0
            target = target_goal.target_value or 0

            # Calculate progress based on direction
            if baseline == target:
                progress = 0
                score = 0
            else:
                # Direction: "increase" means higher is better, "decrease" means lower is better
                if target_goal.direction == TargetGoal.Direction.INCREASE:
                    # Progress = (current - baseline) / (target - baseline) * 100
                    if target > baseline:
                        progress = max(0, min(100, ((total_value - baseline) / (target - baseline) * 100)))
                    else:
                        progress = 0
                else:  # decrease
                    # Progress = (baseline - current) / (baseline - target) * 100
                    if baseline > target:
                        progress = max(0, min(100, ((baseline - total_value) / (baseline - target) * 100)))
                    else:
                        progress = 0

            # Determine status
            if progress >= 76:
                status = IndicatorScore.ScoreStatus.ACHIEVED
            elif progress >= 51:
                status = IndicatorScore.ScoreStatus.ON_TRACK
            elif progress >= 26:
                status = IndicatorScore.ScoreStatus.AT_RISK
            else:
                status = IndicatorScore.ScoreStatus.POOR

            score = progress

        return _create_or_update_indicator_score(
            organization=organization,
            indicator=indicator,
            reporting_period=reporting_period,
            score=score,
            value=total_value,
            baseline=baseline,
            target=target,
            progress=progress,
            status=status,
            calculation_method="linear_progress",
        )

    except Exception as e:
        logger.error(f"Error calculating indicator score: {str(e)}", exc_info=True)
        raise


@transaction.atomic
def calculate_all_indicator_scores(
    organization: Organization,
    reporting_period: ReportingPeriod
) -> list:
    """
    Calculate indicator scores for all indicators in an organization.

    Args:
        organization: Organization
        reporting_period: Reporting period

    Returns:
        List of IndicatorScore objects
    """

    try:
        indicators = Indicator.objects.filter(is_active=True)
        scores = []

        for indicator in indicators:
            score = calculate_indicator_score(organization, indicator, reporting_period)
            scores.append(score)

        logger.info(f"Calculated {len(scores)} indicator scores for {organization.name}")
        return scores

    except Exception as e:
        logger.error(f"Error batch calculating indicator scores: {str(e)}", exc_info=True)
        raise


@transaction.atomic
def batch_calculate_indicator_scores(
    organizations: list,
    reporting_period: ReportingPeriod
) -> int:
    """
    Calculate indicator scores for multiple organizations.

    Args:
        organizations: List of Organization objects
        reporting_period: Reporting period

    Returns:
        Total count of scores calculated
    """

    try:
        total = 0
        for org in organizations:
            scores = calculate_all_indicator_scores(org, reporting_period)
            total += len(scores)

        logger.info(f"Calculated {total} indicator scores across {len(organizations)} organizations")
        return total

    except Exception as e:
        logger.error(f"Error in batch processing: {str(e)}", exc_info=True)
        raise


def _create_or_update_indicator_score(
    organization,
    indicator,
    reporting_period,
    score,
    value,
    baseline,
    target,
    progress,
    status,
    calculation_method,
):
    """Create or update an indicator score record."""

    indicator_score, created = IndicatorScore.objects.update_or_create(
        organization=organization,
        indicator=indicator,
        reporting_period=reporting_period,
        defaults={
            'score': round(score, 2),
            'value': value,
            'baseline': baseline,
            'target': target,
            'progress': round(progress, 2),
            'status': status,
            'calculation_method': calculation_method,
            'is_manual': False,
            'calculated_at': timezone.now(),
        }
    )

    action = "Created" if created else "Updated"
    logger.info(
        f"{action} indicator score for {organization.name}/{indicator.name}: "
        f"score={score:.1f}, status={status}, progress={progress:.1f}%"
    )

    return indicator_score
