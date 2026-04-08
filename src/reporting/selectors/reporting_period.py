from datetime import date
from typing import Optional

from submissions.models import ReportingPeriod
from targets.models import TargetGoal
from targets.selectors.reporting_periods import get_target_reporting_periods


def get_active_reporting_period_for_target(organization, target: TargetGoal) -> Optional[ReportingPeriod]:
    """
    Return the active (OPEN) reporting period for a target within an organization.

    Logic:
    - Ensure reporting periods for the target exist (via targets selector)
    - From those periods, return the first period that is OPEN and whose date range
      includes today. If none matches by date, return the first OPEN period.
    - If none found, return None.
    """
    # Ensure periods exist for the target (this returns list)
    periods = get_target_reporting_periods(target)

    today = date.today()

    # Prefer OPEN periods that cover today
    for p in periods:
        if p.status == ReportingPeriod.Status.OPEN and p.start_date <= today <= p.end_date:
            return p

    # Otherwise return any OPEN period for the target
    for p in periods:
        if p.status == ReportingPeriod.Status.OPEN:
            return p

    return None
