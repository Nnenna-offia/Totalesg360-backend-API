from typing import Optional
from decimal import Decimal
from django.db import transaction

from indicators.models import Indicator
from submissions.models import DataSubmission
from emissions.selectors.queries import get_scope1_emissions, get_scope2_emissions, get_scope3_emissions, get_total_emissions


INDICATOR_CODE_MAP = {
    'total_scope1_emissions': get_scope1_emissions,
    'total_scope2_emissions': get_scope2_emissions,
    'total_scope3_emissions': get_scope3_emissions,
    'total_emissions': get_total_emissions,
}


def persist_emission_indicators(org, reporting_period, by_user: Optional[object] = None, submit: bool = True):
    """Compute emission aggregates and upsert DataSubmission rows for matching indicators.

    - `org`: Organization instance
    - `reporting_period`: ReportingPeriod instance
    - `by_user`: optional User instance to mark `submitted_by`
    - `submit`: if True, mark status as SUBMITTED, otherwise DRAFT
    """
    codes = list(INDICATOR_CODE_MAP.keys())
    indicators = {ind.code: ind for ind in Indicator.objects.filter(code__in=codes)}

    results = {}
    for code, func in INDICATOR_CODE_MAP.items():
        ind = indicators.get(code)
        if not ind:
            continue
        total = func(org, reporting_period)
        # normalize to Decimal/float
        try:
            total_value = float(total or 0)
        except Exception:
            total_value = 0.0

        defaults = {
            'value_number': total_value,
            'value_text': None,
            'value_boolean': None,
            'metadata': {},
            'status': DataSubmission.Status.SUBMITTED if submit else DataSubmission.Status.DRAFT,
            'submitted_by': by_user if submit else None,
            'submitted_at': None,
            'approved_by': None,
            'approved_at': None,
        }

        with transaction.atomic():
            obj, created = DataSubmission.objects.update_or_create(
                organization=org,
                indicator=ind,
                reporting_period=reporting_period,
                facility=None,
                defaults=defaults,
            )
        results[code] = obj

    return results
