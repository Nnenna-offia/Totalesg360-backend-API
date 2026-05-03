from decimal import Decimal
import logging
from django.db import transaction
from django.db.models import Q
from activities.models.scope import Scope
from emissions.models.emission_factor import EmissionFactor
from emissions.models.calculated_emission import CalculatedEmission
from emissions.services.indicator_traceability import get_expected_scope_code_for_input


logger = logging.getLogger(__name__)


def _find_best_factor(activity_type, org_country, year):
    # Prefer indicator-linked factors, then activity-type factors.
    indicator = getattr(activity_type, "indicator", None)
    if indicator is not None:
        qs = EmissionFactor.objects.filter(Q(indicator=indicator) | Q(activity_type=activity_type))
    else:
        qs = EmissionFactor.objects.filter(activity_type=activity_type)
    # try exact match
    f = qs.filter(country=org_country, year=year).first()
    if f:
        return f
    # try any country match for year
    f = qs.filter(year=year).first()
    if f:
        return f
    # fallback to country-agnostic
    f = qs.filter(country__isnull=True).order_by('-year').first()
    return f


def calculate_and_store(activity_submission):
    """Calculate emissions for an ActivitySubmission and store a CalculatedEmission.

    Returns the CalculatedEmission instance.
    """
    activity_type = activity_submission.activity_type
    org = activity_submission.organization
    facility = activity_submission.facility
    year = activity_submission.reporting_period.year

    factor = _find_best_factor(activity_type, getattr(org, 'country', None), year)
    if not factor:
        # No factor found; do not create calculation but return None
        return None

    input_indicator_code = getattr(getattr(activity_type, "indicator", None), "code", None)
    expected_scope_code = get_expected_scope_code_for_input(input_indicator_code)
    scope_for_emission = activity_type.scope

    # Traceability is part of emission calculation logic: input indicator -> derived scope.
    if expected_scope_code:
        resolved_scope = Scope.objects.filter(code=expected_scope_code).first()
        if resolved_scope:
            scope_for_emission = resolved_scope
            if getattr(activity_type.scope, "code", None) != expected_scope_code:
                logger.warning(
                    "Activity scope differs from traceability scope; using traceability scope",
                    extra={
                        "activity_type_id": str(activity_type.id),
                        "activity_scope": getattr(activity_type.scope, "code", None),
                        "expected_scope": expected_scope_code,
                        "input_indicator_code": input_indicator_code,
                    },
                )
        else:
            logger.warning(
                "Traceability scope code not found in Scope table",
                extra={
                    "expected_scope": expected_scope_code,
                    "input_indicator_code": input_indicator_code,
                },
            )
    else:
        logger.warning(
            "No traceability mapping found for input indicator during emission calculation",
            extra={
                "activity_type_id": str(activity_type.id),
                "input_indicator_code": input_indicator_code,
            },
        )

    # compute
    value = Decimal(activity_submission.value)
    emission_value = (value * Decimal(factor.effective_factor_value)).quantize(Decimal('0.000001'))

    with transaction.atomic():
        obj, created = CalculatedEmission.objects.update_or_create(
            activity_submission=activity_submission,
            defaults={
                'organization': org,
                'facility': facility,
                'emission_factor': factor,
                'scope': scope_for_emission,
                'emission_value': emission_value,
                'reporting_period': activity_submission.reporting_period,
            }
        )

    return obj
