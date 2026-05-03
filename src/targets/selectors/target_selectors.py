from typing import List, Optional
from django.db.models import Sum

from targets.models import TargetGoal, TargetMilestone
from indicators.models import IndicatorValue
from submissions.models import ReportingPeriod


def get_goals_for_organization(org) -> List[TargetGoal]:
    return list(TargetGoal.objects.filter(organization=org).select_related('indicator', 'facility'))


def get_goal_milestones(goal: TargetGoal) -> List[TargetMilestone]:
    return list(goal.milestones.all())


def get_indicator_current_value(indicator, org, period: Optional[ReportingPeriod] = None, period_type: Optional[str] = None):
    """Return current numeric value from IndicatorValue for an org+indicator.

    If `period` is provided, aggregate all facility values in that period.
    Otherwise aggregate values from active reporting period(s).
    """
    qs = IndicatorValue.objects.filter(organization=org, indicator=indicator)
    if period:
        qs = qs.filter(reporting_period=period)
    else:
        qs = qs.filter(reporting_period__is_active=True)
        if period_type:
            qs = qs.filter(reporting_period__period_type=period_type)

    total = qs.aggregate(total=Sum('value')).get('total')
    return float(total) if total is not None else None
