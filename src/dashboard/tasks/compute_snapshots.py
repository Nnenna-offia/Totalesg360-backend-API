from celery import shared_task
import time
from django.utils import timezone

from organizations.models import Organization
from dashboard.models import DashboardMetric, IndicatorSnapshot, TargetSnapshot
from dashboard.selectors.dashboard_selectors import get_emissions_summary, get_indicator_values, get_compliance_summary
from targets.selectors.target_selectors import get_goals_for_organization, get_goal_milestones
from targets.services.target_progress_service import calculate_target_progress


@shared_task(name='dashboard.compute_snapshots')
def compute_snapshots(chunk_size: int = 50, pause_seconds: float = 0.1):
    """Compute and persist snapshot rows for all organizations.

    - Paginate organizations to avoid memory spikes.
    - Write per-indicator and per-target snapshot rows, and a summarized DashboardMetric.
    """
    snapshot_time = timezone.now()
    created = 0
    qs = Organization.objects.all().order_by('name')
    index = 0
    total = qs.count()
    while index < total:
        batch = qs[index : index + chunk_size]
        for org in batch:
            try:
                # indicators
                indicators = get_indicator_values(org)
                # indicators is expected to be iterable of dicts with 'indicator' and 'value'
                for r in indicators:
                    ind = r.get('indicator') or r.get('indicator__id') or r.get('indicator_id')
                    val = r.get('value')
                    unit = r.get('unit') or ''
                    if ind is None:
                        continue
                    indicator_obj = None
                    if hasattr(r.get('indicator'), 'id'):
                        indicator_obj = r.get('indicator')
                    else:
                        # if ind is an identifier, try to resolve the Indicator instance
                        try:
                            from indicators.models import Indicator
                            indicator_obj = Indicator.objects.get(id=ind)
                        except Exception:
                            indicator_obj = None
                    if indicator_obj is None:
                        # skip if we cannot resolve an Indicator instance
                        continue
                    IndicatorSnapshot.objects.update_or_create(
                        organization=org,
                        indicator=indicator_obj,
                        reporting_period=None,
                        defaults={'value': val, 'unit': unit, 'calculated_at': snapshot_time},
                    )
            except Exception:
                pass

            try:
                # targets
                goals = get_goals_for_organization(org)
                for g in goals:
                    prog = calculate_target_progress(g)
                    TargetSnapshot.objects.update_or_create(
                        organization=org,
                        target=g,
                        reporting_period=None,
                        defaults={'current_value': prog.get('current_value') if isinstance(prog, dict) else None,
                                  'progress_percent': prog.get('progress_percent') if isinstance(prog, dict) else None,
                                  'status': prog.get('status') if isinstance(prog, dict) else '',
                                  'calculated_at': snapshot_time},
                    )
            except Exception:
                pass

            try:
                # dashboard metrics (simple composition)
                env = get_emissions_summary(org)
                total_emissions = sum(env.values()) if isinstance(env, dict) else 0.0
                emissions_score = max(0, 100 - (total_emissions / 1000.0)) if total_emissions else 100
                # we don't currently have social/governance detailed scoring; keep placeholders
                dm, _ = DashboardMetric.objects.update_or_create(
                    organization=org,
                    reporting_period=None,
                    defaults={
                        'environmental_score': emissions_score,
                        'social_score': 50.0,
                        'governance_score': 50.0,
                        'overall_esg_score': (emissions_score * 0.6) + (50 * 0.2) + (50 * 0.2),
                        'calculated_at': snapshot_time,
                    }
                )
            except Exception:
                pass

            created += 1

        index += chunk_size
        time.sleep(pause_seconds)

    return {'created_orgs': created, 'snapshot_time': str(snapshot_time)}
