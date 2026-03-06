from typing import Optional
from django.db.models import Prefetch

from indicators.selectors.queries import get_org_effective_indicators
from submissions.models import DataSubmission, ReportingPeriod


def get_indicator_submission(org, indicator, period: ReportingPeriod) -> Optional[DataSubmission]:
    return DataSubmission.objects.filter(organization=org, indicator=indicator, reporting_period=period).first()


def get_period_submissions(org, period: ReportingPeriod, pillar: Optional[str] = None,
                           indicator_code: Optional[str] = None,
                           submission_status: Optional[str] = None,
                           facility_id: Optional[str] = None):
    """Return indicators for the org annotated with existing submission values for the period.

    This joins `get_org_effective_indicators` and left-joins `DataSubmission` to produce a list
    of indicators with `is_required_effective` and `current_submission` attachment.
    """
    indicators_qs = get_org_effective_indicators(org)
    if pillar:
        indicators_qs = indicators_qs.filter(pillar=pillar)

    # Prefetch submissions for the period
    submissions_qs = DataSubmission.objects.filter(organization=org, reporting_period=period)
    # apply submission-level filters to the prefetch queryset where possible
    if submission_status:
        submissions_qs = submissions_qs.filter(status=submission_status)
    if facility_id:
        submissions_qs = submissions_qs.filter(facility_id=facility_id)
    indicators_qs = indicators_qs.prefetch_related(Prefetch('submissions', queryset=submissions_qs, to_attr='period_submissions'))

    results = []
    for ind in indicators_qs:
        submission = ind.period_submissions[0] if getattr(ind, 'period_submissions', None) else None
        results.append({
            'indicator': ind,
            'is_required_effective': getattr(ind, 'is_required_effective', False),
            'is_active_effective': getattr(ind, 'is_active_effective', True),
            'submission': submission,
        })

    # If caller requested filtering by indicator_code, apply it now (indicator-level field)
    if indicator_code:
        results = [r for r in results if getattr(r.get('indicator'), 'code', None) == indicator_code]

    # If submission-level filters were applied to the prefetch, exclude indicators with no matching submission
    if submission_status or facility_id:
        results = [r for r in results if r.get('submission') is not None]

    return results
