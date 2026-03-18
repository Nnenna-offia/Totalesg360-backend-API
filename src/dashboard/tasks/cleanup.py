from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

from django.db import DatabaseError, ProgrammingError
from dashboard.models import DashboardSnapshot, EmissionSnapshot, IndicatorSnapshot, TargetSnapshot, ComplianceSnapshot, DashboardMetric
from dashboard.startup import wait_for_tables

logger = logging.getLogger(__name__)


# Ensure workers wait briefly for migrations/tables before running cleanup
wait_for_tables([
    'dashboard_dashboardsnapshot',
    'dashboard_targetsnapshot',
    'dashboard_emissionsnapshot',
    'dashboard_indicatorsnapshot',
    'dashboard_compliancesnapshot',
], timeout=30, interval=1.0)


def _batched_delete(qs, batch_size: int = 1000) -> int:
    """Delete queryset in batches and return total deleted count."""
    total = 0
    while True:
        pks = list(qs.values_list('pk', flat=True)[:batch_size])
        if not pks:
            break
        deleted, _ = qs.model.objects.filter(pk__in=pks).delete()
        total += deleted
    return total


@shared_task(name='dashboard.cleanup_old_snapshots')
def cleanup_old_snapshots(retention_days: int = 365, batch_size: int = 1000):
    """Delete snapshots older than `retention_days` using batched deletes.

    Returns counts deleted per model. Resilient to missing tables/DB errors.
    """
    cutoff = timezone.now() - timedelta(days=retention_days)
    results = {}
    models = [DashboardMetric, DashboardSnapshot, EmissionSnapshot, IndicatorSnapshot, TargetSnapshot, ComplianceSnapshot]
    for model in models:
        try:
            qs = model.objects.filter(snapshot_date__lt=cutoff)
            # count may be expensive; we delete in batches and sum deleted rows
            deleted = _batched_delete(qs, batch_size=batch_size)
            results[model.__name__] = deleted
        except (ProgrammingError, DatabaseError) as exc:
            logger.exception('Failed to cleanup snapshots for %s: %s', model.__name__, exc)
            results[model.__name__] = 0
        except Exception as exc:
            logger.exception('Unexpected error when cleaning %s: %s', model.__name__, exc)
            results[model.__name__] = 0
    return results
