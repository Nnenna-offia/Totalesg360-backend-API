from rest_framework.exceptions import ValidationError
from submissions.models import ReportingPeriod
from reporting.selectors.reporting_period import get_active_reporting_period_for_target


def get_or_raise_active_reporting_period(organization, target):
    """Return the active reporting period for a target or raise ValidationError."""
    period = get_active_reporting_period_for_target(organization, target)
    if period is None:
        raise ValidationError("No active reporting period found for this target")
    return period
