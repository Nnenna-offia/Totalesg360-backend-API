from typing import Dict, Any, Optional

from dashboard.selectors.dashboard_selectors import (
    get_emissions_summary,
    get_social_metrics,
    get_governance_metrics,
    get_compliance_summary,
)
from dashboard.models import DashboardMetric
from django.db import ProgrammingError, DatabaseError
from django.db import connection


def get_dashboard_summary(org, period=None, facility_id: Optional[str] = None) -> Dict[str, Any]:
    # Prefer precomputed DashboardMetric if available
    try:
        if 'dashboard_dashboardmetric' in connection.introspection.table_names():
            metric = DashboardMetric.objects.filter(organization=org, reporting_period=period).order_by('-calculated_at').first()
        else:
            metric = None
    except (ProgrammingError, DatabaseError):
        metric = None

    if metric:
        comp = get_compliance_summary(org)
        return {
            'environment': {'score': metric.environmental_score},
            'social': {'score': metric.social_score},
            'governance': {'score': metric.governance_score},
            'compliance': comp,
            'overall_esg_score': metric.overall_esg_score,
        }

    # fallback to live computation when snapshot not available
    env = get_emissions_summary(org, period=period, facility_id=facility_id)
    soc = get_social_metrics(org, period=period)
    gov = get_governance_metrics(org, period=period)
    comp = get_compliance_summary(org)

    # simple scoring: normalize emissions into a 0-100 inverted score
    total_emissions = sum(env.values()) if isinstance(env, dict) else 0.0
    emissions_score = max(0, 100 - (total_emissions / 1000.0)) if total_emissions else 100

    overall = (emissions_score * 0.6) + (50 * 0.2) + (50 * 0.2)

    return {
        'environment': {'emissions': env, 'score': emissions_score},
        'social': {'metrics': soc, 'score': 50},
        'governance': {'metrics': gov, 'score': 50},
        'compliance': comp,
        'overall_esg_score': overall,
    }
