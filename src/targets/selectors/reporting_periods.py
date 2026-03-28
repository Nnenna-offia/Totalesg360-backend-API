"""
Target Reporting Periods Selector

Dynamically resolves ReportingPeriods for a target goal based on:
- Organization
- Reporting frequency
- Baseline year to target year range
- Auto-generates missing periods
"""
from typing import List
from submissions.models import ReportingPeriod
from targets.models import TargetGoal


def get_target_reporting_periods(goal: TargetGoal) -> List[ReportingPeriod]:
    """
    Dynamically fetch ReportingPeriods matching a target goal's reporting frequency and year range.
    
    Automatically ensures periods exist for the target's year range.
    
    Args:
        goal: TargetGoal instance
        
    Returns:
        List of ReportingPeriod instances for the target, ordered by start_date
        
    Example:
        target: Quarterly 2025 → 2028
        Returns: 16 quarters (Q1-Q4 for each year)
    """
    from targets.services.reporting_period_service import ensure_reporting_periods_exist
    
    # Ensure all required periods exist
    ensure_reporting_periods_exist(
        organization=goal.organization,
        start_year=goal.baseline_year,
        end_year=goal.target_year,
        frequency=goal.reporting_frequency
    )
    
    # Query periods matching the frequency and year range
    periods = ReportingPeriod.objects.filter(
        organization=goal.organization,
        period_type=goal.reporting_frequency,
        start_date__year__gte=goal.baseline_year,
        end_date__year__lte=goal.target_year,
        is_active=True
    ).order_by("start_date")
    
    return list(periods)
