from typing import Iterable, Set, List
from django.db.models import Q

# Import existing models
from indicators.models import Indicator, IndicatorValue
from compliance.models import IndicatorFrameworkMapping


def get_required_indicators(framework) -> List[Indicator]:
    """Return indicators required by the given framework.

    `framework` may be a Framework instance or its id.
    """
    qs = (
        IndicatorFrameworkMapping.objects
        .select_related('indicator', 'requirement')
        .filter(
            requirement__framework=framework,
            requirement__is_mandatory=True,
            is_active=True,
            is_primary=True,
            mapping_type=IndicatorFrameworkMapping.MappingType.PRIMARY,
        )
    )
    return list(set(ifm.indicator for ifm in qs))  # dedup since multiple requirements can require same indicator


def get_submitted_indicators(organization, period) -> List[Indicator]:
    """Return indicators that have at least one IndicatorValue for the org+period.

    Uses IndicatorValue as the single source of truth so that both activity-based
    and direct-submission paths are captured correctly.
    """
    indicator_ids = (
        IndicatorValue.objects
        .filter(organization=organization, reporting_period=period)
        .values_list("indicator_id", flat=True)
        .distinct()
    )
    return list(Indicator.objects.filter(id__in=indicator_ids))


def get_missing_indicators(organization, framework, period) -> List[Indicator]:
    required = set(get_required_indicators(framework))
    submitted = set(get_submitted_indicators(organization, period))
    missing = required - submitted
    return list(missing)


def get_optional_completed(organization, framework, period) -> List[Indicator]:
    """Return indicators that are optional for the framework but were submitted."""
    optional_qs = (
        IndicatorFrameworkMapping.objects
        .select_related('indicator', 'requirement')
        .filter(requirement__framework=framework, requirement__is_mandatory=False, is_active=True)
    )
    optional_indicators = {ifm.indicator for ifm in optional_qs}
    submitted = set(get_submitted_indicators(organization, period))
    return list(optional_indicators & submitted)
