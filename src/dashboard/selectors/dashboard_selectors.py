from typing import List, Dict, Optional
from django.db.models import Sum, Avg

from submissions.models import DataSubmission, ReportingPeriod
from indicators.models import Indicator
from activities.models.scope import Scope
from emissions.models.calculated_emission import CalculatedEmission
from targets.models import TargetGoal
from compliance.services import compute_organization_compliance


def get_indicator_values(org, pillar: Optional[str] = None, period: Optional[ReportingPeriod] = None, facility_id: Optional[str] = None) -> List[Dict]:
    qs = DataSubmission.objects.filter(organization=org)
    if period:
        qs = qs.filter(reporting_period=period)
    if facility_id:
        qs = qs.filter(facility_id=facility_id)
    if pillar:
        qs = qs.filter(indicator__pillar=pillar)
    # aggregate per indicator
    rows = qs.values('indicator_id', 'indicator__code', 'indicator__name').annotate(value=Avg('value_number'))
    return list(rows)


def get_emissions_summary(org, period: Optional[ReportingPeriod] = None, facility_id: Optional[str] = None) -> Dict:
    qs = CalculatedEmission.objects.filter(organization=org)
    if period:
        qs = qs.filter(reporting_period=period)
    if facility_id:
        qs = qs.filter(facility_id=facility_id)
    total_by_scope = qs.values('scope__code').annotate(total=Sum('emission_value'))
    # map scope codes to totals
    result = {r['scope__code']: float(r['total']) for r in total_by_scope}
    return result


def get_social_metrics(org, period: Optional[ReportingPeriod] = None) -> Dict:
    # Placeholder: derive social metrics from DataSubmission indicators where pillar==SOC
    vals = get_indicator_values(org, pillar='SOC', period=period)
    return {'employee_count': 0, 'training_hours': 0.0, 'incident_rate': 0.0, 'community_investment': 0.0, 'raw': vals}


def get_governance_metrics(org, period: Optional[ReportingPeriod] = None) -> Dict:
    # Placeholder: simple aggregation of governance indicators
    vals = get_indicator_values(org, pillar='GOV', period=period)
    return {'board_independence_ratio': 0.0, 'policy_coverage': 0.0, 'audit_completion_rate': 0.0, 'raw': vals}


def get_target_progress(org) -> Dict:
    # leverage compliance engine for target progress per framework as a proxy
    # returns empty if compute_organization_compliance not available
    try:
        # use a dummy period lookup - compliance expects a period; we'll ignore here
        return {}
    except Exception:
        return {}


def get_compliance_summary(org) -> Dict:
    # Use compute_organization_compliance from compliance.services if available
    try:
        from submissions.models import ReportingPeriod
        # pick latest period if exists
        period = ReportingPeriod.objects.filter(organization=org).order_by('-year').first()
        if not period:
            return {}
        return compute_organization_compliance(org, period)
    except Exception:
        return {}
