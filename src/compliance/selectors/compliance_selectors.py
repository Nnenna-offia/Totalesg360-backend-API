from typing import Iterable, Set, List
from django.db.models import Q

# Import existing models
from indicators.models import FrameworkIndicator, Indicator
from submissions.models import DataSubmission


def get_required_indicators(framework) -> List[Indicator]:
    """Return indicators required by the given framework.

    `framework` may be a Framework instance or its id.
    """
    qs = FrameworkIndicator.objects.select_related('indicator').filter(framework=framework, is_required=True)
    return [fi.indicator for fi in qs]


def get_submitted_indicators(organization, period) -> List[Indicator]:
    """Return indicators that have at least one DataSubmission for the org+period."""
    qs = DataSubmission.objects.filter(
        organization=organization,
        reporting_period=period,
    ).select_related('indicator')
    indicators = {ds.indicator for ds in qs}
    return list(indicators)


def get_missing_indicators(organization, framework, period) -> List[Indicator]:
    required = set(get_required_indicators(framework))
    submitted = set(get_submitted_indicators(organization, period))
    missing = required - submitted
    return list(missing)


def get_optional_completed(organization, framework, period) -> List[Indicator]:
    """Return indicators that are optional for the framework but were submitted."""
    optional_qs = FrameworkIndicator.objects.select_related('indicator').filter(framework=framework, is_required=False)
    optional_indicators = {fi.indicator for fi in optional_qs}
    submitted = set(get_submitted_indicators(organization, period))
    return list(optional_indicators & submitted)
