from celery import shared_task
from django.utils import timezone
import time

from organizations.models import Organization
from dashboard.models import (
    DashboardSnapshot,
    EmissionSnapshot,
    IndicatorSnapshot,
    TargetSnapshot,
    ComplianceSnapshot,
)
from dashboard.services.dashboard_service import get_dashboard_summary
from dashboard.selectors.dashboard_selectors import get_emissions_summary, get_indicator_values, get_compliance_summary
from targets.selectors.target_selectors import get_goals_for_organization, get_goal_milestones
from targets.services.target_progress_service import calculate_target_progress
import logging

logger = logging.getLogger(__name__)


@shared_task(name='dashboard.populate_snapshots')
def populate_dashboard_snapshots(snapshot_date: str = None, chunk_size: int = 100, pause_seconds: float = 0.2):
    """Populate snapshots for all organizations in paginated chunks.

    - Paginate organizations by `chunk_size` to avoid loading all orgs into memory.
    - Sleep `pause_seconds` between chunks as a simple rate-limit.
    - Compute richer target and indicator snapshots using existing selectors/services.
    """
    snapshot_date = timezone.now() if snapshot_date is None else snapshot_date
    created = 0

    qs = Organization.objects.all().order_by('name')
    index = 0
    total = qs.count()
    while index < total:
        batch = qs[index : index + chunk_size]
        for org in batch:
            # no-op placeholder: we'll create JSON snapshots later if necessary

            # Dashboard summary
            try:
                summary = get_dashboard_summary(org)
                DashboardSnapshot.objects.create(
                    organization=org,
                    snapshot_date=snapshot_date,
                    data=summary,
                    source='nightly_job',
                )
            except Exception as exc:
                logger.exception('Failed to create DashboardSnapshot for %s: %s', getattr(org, 'name', str(org)), exc)
                summary = {}

            # Emissions snapshot
            try:
                emissions = get_emissions_summary(org)
                EmissionSnapshot.objects.create(
                    organization=org,
                    snapshot_date=snapshot_date,
                    data=emissions,
                    source='nightly_job',
                )
            except Exception as exc:
                logger.exception('Failed to create EmissionSnapshot for %s: %s', getattr(org, 'name', str(org)), exc)

            # Indicator snapshot: include pillar aggregates and top indicators
            try:
                indicators = get_indicator_values(org)
                # produce simple aggregates: avg per pillar
                pillar_map = {}
                for r in indicators:
                    pill = r.get('indicator__pillar') or r.get('pillar') or 'UNKNOWN'
                    pillar_map.setdefault(pill, []).append(r.get('value'))
                pillar_agg = {k: (sum(v) / len(v) if v else 0) for k, v in pillar_map.items()}
                IndicatorSnapshot.objects.create(
                    organization=org,
                    snapshot_date=snapshot_date,
                    data={'pillar_averages': pillar_agg, 'raw': indicators},
                    source='nightly_job',
                )
            except Exception as exc:
                logger.exception('Failed to create IndicatorSnapshot for %s: %s', getattr(org, 'name', str(org)), exc)

            # Targets snapshot: compute per-goal progress and store as a JSON summary
            try:
                goals = get_goals_for_organization(org)
                goal_items = []
                for g in goals:
                    prog = calculate_target_progress(g)
                    milestones = [
                        {'year': m.year, 'target_value': m.target_value} for m in get_goal_milestones(g)
                    ]
                    goal_items.append({'goal_id': str(g.id), 'name': g.name, 'indicator': g.indicator.code if g.indicator else None, 'progress': prog, 'milestones': milestones})

                # Create a single JSON-backed TargetSnapshot to match current migrations
                TargetSnapshot.objects.create(
                    organization=org,
                    snapshot_date=snapshot_date,
                    data={'goals': goal_items},
                    source='nightly_job',
                )
            except Exception as exc:
                logger.exception('Failed to create TargetSnapshot(s) for %s: %s', getattr(org, 'name', str(org)), exc)

            # Compliance snapshot
            try:
                comp = get_compliance_summary(org)
                ComplianceSnapshot.objects.create(
                    organization=org,
                    snapshot_date=snapshot_date,
                    data=comp,
                    source='nightly_job',
                )
            except Exception as exc:
                logger.exception('Failed to create ComplianceSnapshot for %s: %s', getattr(org, 'name', str(org)), exc)

                # if no per-indicator snapshots were created, create a JSON placeholder
                try:
                    if not IndicatorSnapshot.objects.filter(organization=org).exists():
                        IndicatorSnapshot.objects.create(
                            organization=org,
                            snapshot_date=snapshot_date,
                            data={'pillar_averages': {}, 'raw': []},
                            source='nightly_job',
                        )
                except Exception as exc:
                    logger.exception('Failed to create placeholder IndicatorSnapshot for %s: %s', getattr(org, 'name', str(org)), exc)

                # if no target snapshots created, add JSON placeholder
                try:
                    if not TargetSnapshot.objects.filter(organization=org).exists():
                        TargetSnapshot.objects.create(
                            organization=org,
                            snapshot_date=snapshot_date,
                            data={'goals': []},
                            source='nightly_job',
                        )
                except Exception as exc:
                    logger.exception('Failed to create placeholder TargetSnapshot for %s: %s', getattr(org, 'name', str(org)), exc)

                created += 1

        index += chunk_size
        # rate-limit between batches
        time.sleep(pause_seconds)

    return {'created_orgs': created, 'snapshot_date': str(snapshot_date)}
