from typing import List, Optional
from django.db.models import Max

from targets.models import TargetGoal, TargetMilestone
from submissions.models import DataSubmission, ReportingPeriod


def get_goals_for_organization(org) -> List[TargetGoal]:
    return list(TargetGoal.objects.filter(organization=org).select_related('indicator', 'facility'))


def get_goal_milestones(goal: TargetGoal) -> List[TargetMilestone]:
    return list(goal.milestones.all())


def get_indicator_current_value(indicator, org, period: Optional[ReportingPeriod] = None):
    """Return the latest submitted value for indicator for org and optional period.

    If `period` is provided, return submissions within that reporting period.
    Otherwise return the most recent DataSubmission.value_number for that org+indicator.
    """
    qs = DataSubmission.objects.filter(organization=org, indicator=indicator)
    if period:
        qs = qs.filter(reporting_period=period)
    # prefer submitted/approved values; use value_number for numeric indicators
    ds = qs.order_by('-submitted_at').first()
    if not ds:
        return None
    # infer numeric value field
    if ds.value_number is not None:
        return ds.value_number
    if ds.value_boolean is not None:
        return 1.0 if ds.value_boolean else 0.0
    # fallback: None for non-numeric
    return None
