from django.db.models import Sum
from emissions.models.calculated_emission import CalculatedEmission
from activities.models.scope import Scope


def _sum_for_scope(org, period, scope_code=None):
    qs = CalculatedEmission.objects.filter(organization=org, reporting_period=period)
    if scope_code:
        qs = qs.filter(scope__code=scope_code)
    agg = qs.aggregate(total=Sum('emission_value'))
    return agg['total'] or 0


def get_scope1_emissions(org, period):
    return _sum_for_scope(org, period, scope_code='scope1')


def get_scope2_emissions(org, period):
    return _sum_for_scope(org, period, scope_code='scope2')


def get_scope3_emissions(org, period):
    return _sum_for_scope(org, period, scope_code='scope3')


def get_total_emissions(org, period):
    return _sum_for_scope(org, period, scope_code=None)
