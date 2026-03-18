from typing import Dict, Any, List
from decimal import Decimal

from django.db.models import Count

from compliance.selectors import (
    get_required_indicators,
    get_submitted_indicators,
    get_missing_indicators,
    get_optional_completed,
)


def _percent(num: int, denom: int) -> int:
    if denom <= 0:
        return 0
    return int(Decimal(num) * 100 / Decimal(denom))


def compute_framework_completion(organization, framework, period) -> Dict[str, Any]:
    required = get_required_indicators(framework)
    submitted = get_submitted_indicators(organization, period)

    required_set = set(required)
    submitted_set = set(submitted)

    submitted_required = len(required_set & submitted_set)
    total_required = len(required_set)
    missing_required = list(sorted([i.id for i in (required_set - submitted_set)]))

    optional_completed = len(get_optional_completed(organization, framework, period))

    completion_percent = _percent(submitted_required, total_required)

    return {
        'framework': getattr(framework, 'name', str(framework)),
        'required_indicators': total_required,
        'submitted_required': submitted_required,
        'missing_required': missing_required,
        'completion_percent': completion_percent,
        'optional_completed': optional_completed,
    }


def compute_organization_compliance(organization, period) -> Dict[str, Any]:
    # iterate frameworks available to the organization via OrganizationFramework
    from organizations.models import OrganizationFramework, RegulatoryFramework as Framework

    frameworks = Framework.objects.filter(
        id__in=OrganizationFramework.objects.filter(organization=organization).values_list('framework_id', flat=True)
    )

    framework_results: List[Dict[str, Any]] = []
    total_required = 0
    total_submitted_required = 0

    for fw in frameworks:
        res = compute_framework_completion(organization, fw, period)
        framework_results.append(res)
        total_required += res['required_indicators']
        total_submitted_required += res['submitted_required']

    overall_completion = _percent(total_submitted_required, total_required) if total_required else 0

    # compute score using required (70%) and optional (30%) weighting across frameworks
    # aggregate optional completion as percent of optional indicators submitted across frameworks
    optional_total = 0
    optional_submitted = 0
    for fw in frameworks:
        req = get_required_indicators(fw)
        all_fi = fw.framework_indicators.all()
        optional_count = all_fi.filter(is_required=False).count()
        optional_total += optional_count
        optional_submitted += len(get_optional_completed(organization, fw, period))

    optional_completion_percent = _percent(optional_submitted, optional_total) if optional_total else 0

    score = int(Decimal(overall_completion) * Decimal('0.7') + Decimal(optional_completion_percent) * Decimal('0.3'))

    return {
        'frameworks': framework_results,
        'overall_completion': overall_completion,
        'optional_completion_percent': optional_completion_percent,
        'score': score,
    }


def get_missing_indicators(organization, framework, period):
    # wrapper to selectors.get_missing_indicators
    from compliance.selectors import get_missing_indicators as _sel_missing
    return _sel_missing(organization, framework, period)


def facility_rollup(organization, framework, period):
    """Return completion per facility as list of dicts {facility_id, completion_percent}."""
    # DataSubmission has facility field
    from submissions.models import DataSubmission
    from indicators.models import FrameworkIndicator

    required_inds = [i.id for i in get_required_indicators(framework)]

    if not required_inds:
        return []

    qs = DataSubmission.objects.filter(
        organization=organization,
        reporting_period=period,
        indicator_id__in=required_inds,
    ).values('facility_id').annotate(submitted_required=Count('indicator', distinct=True))

    total_required = len(required_inds)
    results = []
    for row in qs:
        facility_id = row.get('facility_id')
        submitted = row.get('submitted_required', 0)
        results.append({'facility_id': facility_id, 'completion_percent': _percent(submitted, total_required)})

    return results
