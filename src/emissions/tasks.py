from celery import shared_task

from emissions.services.persist_indicators import persist_emission_indicators
from submissions.models import ReportingPeriod


@shared_task(bind=True)
def persist_emission_indicators_for_period(self, org_id, period_id):
    try:
        period = ReportingPeriod.objects.get(id=period_id)
    except ReportingPeriod.DoesNotExist:
        return {'error': 'period_not_found'}

    persist_emission_indicators(period.organization, period, by_user=None, submit=True)
    return {'status': 'ok', 'period': str(period_id)}


@shared_task(bind=True)
def persist_emission_indicators_for_all_locked(self):
    # find all locked reporting periods and persist indicators
    periods = ReportingPeriod.objects.filter(status=ReportingPeriod.Status.LOCKED)
    results = []
    for p in periods:
        persist_emission_indicators(p.organization, p, by_user=None, submit=True)
        results.append(str(p.id))
    return {'status': 'ok', 'periods': results}
