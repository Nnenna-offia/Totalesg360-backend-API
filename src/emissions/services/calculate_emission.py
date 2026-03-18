from decimal import Decimal
from django.db import transaction
from django.db.models import Q
from emissions.models.emission_factor import EmissionFactor
from emissions.models.calculated_emission import CalculatedEmission


def _find_best_factor(activity_type, org_country, year):
    # Prefer exact country+year, then country+closest year, then global (country=None) entries
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

    # compute
    value = Decimal(activity_submission.value)
    emission_value = (value * Decimal(factor.factor)).quantize(Decimal('0.000001'))

    with transaction.atomic():
        obj, created = CalculatedEmission.objects.update_or_create(
            activity_submission=activity_submission,
            defaults={
                'organization': org,
                'facility': facility,
                'emission_factor': factor,
                'scope': activity_type.scope,
                'emission_value': emission_value,
                'reporting_period': activity_submission.reporting_period,
            }
        )

    return obj
