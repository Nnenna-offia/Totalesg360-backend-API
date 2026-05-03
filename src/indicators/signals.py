import logging
import threading
from contextlib import contextmanager

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from organizations.models import OrganizationFramework
from indicators.services import schedule_sync_for_org

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Thread-local re-entry guard
# ---------------------------------------------------------------------------
# When recalculate_dependent_indicators writes a parent IndicatorValue it
# would re-trigger this same signal, causing redundant scoring tasks and target
# evaluations.  We suppress re-entry with a per-thread flag so that only the
# *original* submission kicks off the full pipeline.

_tls = threading.local()


@contextmanager
def _suppress_recalculation_signal():
    """While active, the IndicatorValue signal skips its recalculation work."""
    already_set = getattr(_tls, 'in_recalculation', False)
    _tls.in_recalculation = True
    try:
        yield
    finally:
        _tls.in_recalculation = already_set


@receiver(post_save, sender=OrganizationFramework)
def _orgframework_saved(sender, instance, **kwargs):
    # schedule a sync for the organization when framework assignment changes
    org = instance.organization
    schedule_sync_for_org(org)


@receiver(post_delete, sender=OrganizationFramework)
def _orgframework_deleted(sender, instance, **kwargs):
    org = instance.organization
    schedule_sync_for_org(org)


@receiver(post_save, sender='indicators.IndicatorValue')
def trigger_esg_recalculation_on_indicator_value(sender, instance, **kwargs):
    """
    Single entry-point for all post-IndicatorValue-save work.

    Execution order (matches task spec):
      1. Recalculate dependent indicators (with signal suppression so parent
         writes don't re-enter this handler).
      2. Evaluate targets for every indicator in the affected dependency chain
         (INPUT indicator + all upstream PRIMARY/DERIVED ancestors).
      3. Queue the ESG scoring Celery chain.

    Re-entry guard: if we are already inside this handler (because a parent
    indicator's IndicatorValue was written by step 1), skip immediately.
    """
    if getattr(_tls, 'in_recalculation', False):
        return

    from indicators.models import Indicator
    from indicators.services.calculation_engine import (
        recalculate_dependent_indicators,
        get_affected_indicators,
    )
    from targets.models import TargetGoal
    from targets.services.target_evaluation_service import evaluate_targets_for_indicator

    org = instance.organization
    period = instance.reporting_period
    indicator = instance.indicator

    # --- Step 1: recalculate dependent (parent) indicators ---
    # Suppress the signal for writes triggered inside this block so we don't
    # get a cascade of repeated pipeline runs.
    if indicator.indicator_type == Indicator.IndicatorType.INPUT:
        try:
            with _suppress_recalculation_signal():
                recalculate_dependent_indicators(
                    indicator=indicator,
                    org=org,
                    period=period,
                )
        except Exception:
            logger.exception(
                "[IndicatorValue signal] Failed to recalculate dependent indicators "
                "for org=%s indicator=%s",
                getattr(instance, 'organization_id', '?'),
                getattr(indicator, 'code', '?'),
            )

    # --- Step 2: evaluate targets for all affected indicators ---
    # Includes the INPUT indicator itself AND every ancestor that was just
    # recomputed (Scope 1, Total Emissions, etc.).
    try:
        affected = get_affected_indicators(indicator)
        target_indicator_ids = set(
            TargetGoal.objects.filter(
                organization=org,
                status=TargetGoal.Status.ACTIVE,
                indicator_id__in=[affected_indicator.id for affected_indicator in affected],
            ).values_list("indicator_id", flat=True)
        )
        total_evaluations = 0
        for ind in affected:
            if ind.id not in target_indicator_ids:
                continue
            total_evaluations += evaluate_targets_for_indicator(
                indicator=ind,
                organization=org,
                reporting_period=period,
            )
        if total_evaluations:
            logger.info(
                "[IndicatorValue signal] Created %d target evaluation(s) across %d indicator(s) "
                "for org=%s period=%s",
                total_evaluations,
                len(affected),
                instance.organization_id,
                instance.reporting_period_id,
            )
    except Exception:
        logger.exception(
            "[IndicatorValue signal] Failed to evaluate targets for org=%s indicator=%s",
            getattr(instance, 'organization_id', '?'),
            getattr(indicator, 'code', '?'),
        )

    # --- Step 3: queue ESG scoring chain ---
    try:
        from esg_scoring.tasks import (
            calculate_org_indicator_scores,
            calculate_org_pillar_scores,
            calculate_org_esg_score,
        )

        org_id = str(instance.organization_id)
        period_id = str(instance.reporting_period_id)

        logger.info(
            "[IndicatorValue signal] Queuing ESG recalculation for org=%s period=%s",
            org_id,
            period_id,
        )

        task = calculate_org_indicator_scores.delay(
            org_id=org_id,
            period_id=period_id,
        )
        task.then(
            calculate_org_pillar_scores.s(org_id=org_id, period_id=period_id)
        ).then(
            calculate_org_esg_score.s(org_id=org_id, period_id=period_id)
        )

    except Exception:
        logger.exception(
            "[IndicatorValue signal] Failed to queue ESG recalculation for org=%s",
            getattr(instance, 'organization_id', '?'),
        )
