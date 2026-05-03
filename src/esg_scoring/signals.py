"""ESG Scoring Signal Handlers - Auto-trigger calculations on data changes."""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import transaction
import logging

from submissions.models import DataSubmission, ReportingPeriod
from targets.models import TargetGoal
from .tasks import (
    calculate_org_indicator_scores,
    calculate_org_pillar_scores,
    calculate_org_esg_score,
    calculate_group_consolidation,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: write IndicatorValue from an approved DataSubmission
# ---------------------------------------------------------------------------

def _write_indicator_value_from_submission(submission: DataSubmission) -> None:
    """Persist the approved DataSubmission value into IndicatorValue.

    IndicatorValue is the single source of truth for reporting, compliance, and
    target evaluation. This ensures the direct-submission path (DataSubmission)
    converges there just like the activity-based path does.

    For boolean/text indicators a sentinel numeric value (1.0) is stored so that
    compliance coverage queries can detect presence without type ambiguity.
    """
    from indicators.models import Indicator, IndicatorValue

    indicator = submission.indicator

    # Determine the numeric value to store
    if indicator.data_type in (
        Indicator.DataType.NUMBER,
        Indicator.DataType.PERCENT,
        Indicator.DataType.CURRENCY,
    ):
        if submission.value_number is None:
            return  # nothing to store
        numeric_value = float(submission.value_number)
    elif indicator.data_type == Indicator.DataType.BOOLEAN:
        numeric_value = 1.0 if submission.value_boolean else 0.0
    else:
        # TEXT or unknown — store a presence sentinel so compliance can detect coverage
        numeric_value = 1.0

    with transaction.atomic():
        IndicatorValue.objects.update_or_create(
            organization=submission.organization,
            indicator=indicator,
            reporting_period=submission.reporting_period,
            facility=submission.facility,
            defaults={
                "value": numeric_value,
                "metadata": {
                    "source": "data_submission",
                    "submission_id": str(submission.id),
                },
            },
        )

    logger.info(
        "[ESG Signals] Wrote IndicatorValue from DataSubmission %s (indicator=%s value=%s)",
        submission.id,
        indicator.code,
        numeric_value,
    )


# ========== DATA SUBMISSION SIGNALS ==========

@receiver(pre_save, sender=DataSubmission)
def track_submission_status_change(sender, instance, **kwargs):
    """Track when submission status changes to APPROVED."""
    try:
        old_instance = DataSubmission.objects.get(pk=instance.pk)
        instance._status_changed = old_instance.status != instance.status
        instance._old_status = old_instance.status
        instance._new_status = instance.status
    except DataSubmission.DoesNotExist:
        # New submission
        instance._status_changed = False
        instance._old_status = None
        instance._new_status = instance.status


@receiver(post_save, sender=DataSubmission)
def trigger_scoring_on_submission_approved(sender, instance, created, **kwargs):
    """
    Trigger ESG scoring pipeline when a data submission is approved.

    Flow:
    1. Write the approved value into IndicatorValue (single source of truth).
    2. Calculate indicator scores for the organization.
    3. Calculate pillar scores based on indicators.
    4. Calculate overall ESG score.
    """
    # Only trigger on APPROVED status
    if instance.status != DataSubmission.Status.APPROVED:
        return

    # --- Step 1: converge DataSubmission value into IndicatorValue ---
    try:
        _write_indicator_value_from_submission(instance)
    except Exception as e:
        logger.error(
            f"[ESG Signals] Failed to write IndicatorValue from DataSubmission {instance.id}: {e}",
            exc_info=True,
        )

    try:
        org_id = instance.organization.id
        reporting_period_id = instance.reporting_period.id
        
        logger.info(
            f"[ESG Signals] DataSubmission approved - triggering recalculation "
            f"for organization {org_id}, period {reporting_period_id}"
        )
        
        # Use transaction to ensure atomicity
        with transaction.atomic():
            # Queue async tasks in sequence (result of one feeds into next)
            # Task 1: Calculate indicator scores
            task1 = calculate_org_indicator_scores.delay(
                org_id=org_id,
                period_id=reporting_period_id
            )
            
            # Chain additional tasks to run after the first completes
            task1.then(
                calculate_org_pillar_scores.s(org_id=org_id, period_id=reporting_period_id)
            ).then(
                calculate_org_esg_score.s(org_id=org_id, period_id=reporting_period_id)
            )
            
            logger.debug(f"[ESG Signals] Queued scoring tasks: {task1.id}")
            
    except Exception as e:
        logger.error(
            f"[ESG Signals] Error triggering scoring on submission approval: {str(e)}",
            exc_info=True
        )


# ========== TARGET GOAL SIGNALS ==========

@receiver(pre_save, sender=TargetGoal)
def track_target_status_change(sender, instance, **kwargs):
    """Track when target goal status changes."""
    try:
        old_instance = TargetGoal.objects.get(pk=instance.pk)
        instance._status_changed = old_instance.status != instance.status
        instance._old_status = old_instance.status
        instance._new_status = instance.status
    except TargetGoal.DoesNotExist:
        # New target
        instance._status_changed = False
        instance._old_status = None
        instance._new_status = instance.status


@receiver(post_save, sender=TargetGoal)
def trigger_scoring_on_target_change(sender, instance, created, **kwargs):
    """
    Trigger ESG scoring recalculation when a target goal is created, updated, or status changes.
    
    Target changes can affect scoring when:
    - New target is created for an indicator
    - Target value is changed
    - Target status changes (ACTIVE/COMPLETED/ARCHIVED)
    
    This affects the overall assessment and baseline calculations.
    """
    try:
        org_id = instance.organization.id
        indicator_id = instance.indicator.id
        
        logger.info(
            f"[ESG Signals] TargetGoal change detected - triggering recalculation "
            f"for organization {org_id}, indicator {indicator_id}"
        )
        
        # Find the current reporting period for this organization
        from submissions.models import ReportingPeriod
        current_period = ReportingPeriod.objects.filter(
            organization_id=org_id,
            status=ReportingPeriod.Status.OPEN
        ).order_by('-created_at').first()
        
        if current_period:
            with transaction.atomic():
                # Re-calculate all scores for this organization
                # (target changes can affect baseline calculations)
                task = calculate_org_indicator_scores.delay(
                    org_id=org_id,
                    period_id=current_period.id
                )
                
                task.then(
                    calculate_org_pillar_scores.s(org_id=org_id, period_id=current_period.id)
                ).then(
                    calculate_org_esg_score.s(org_id=org_id, period_id=current_period.id)
                )
                
                logger.debug(f"[ESG Signals] Queued target-related scoring tasks: {task.id}")
        else:
            logger.warning(
                f"[ESG Signals] No open reporting period found for organization {org_id}, "
                f"skipping target-triggered scoring"
            )
            
    except Exception as e:
        logger.error(
            f"[ESG Signals] Error triggering scoring on target change: {str(e)}",
            exc_info=True
        )


# ========== REPORTING PERIOD SIGNALS ==========

@receiver(pre_save, sender=ReportingPeriod)
def track_period_status_change(sender, instance, **kwargs):
    """Track when reporting period status changes."""
    try:
        old_instance = ReportingPeriod.objects.get(pk=instance.pk)
        instance._status_changed = old_instance.status != instance.status
        instance._old_status = old_instance.status
        instance._new_status = instance.status
    except ReportingPeriod.DoesNotExist:
        # New period
        instance._status_changed = False
        instance._old_status = None
        instance._new_status = instance.status


@receiver(post_save, sender=ReportingPeriod)
def trigger_consolidation_on_period_close(sender, instance, created, **kwargs):
    """
    Trigger group consolidation when a reporting period is locked or submitted.
    
    Group consolidation should only happen when:
    - Period status changes to LOCKED or SUBMITTED
    - All subsidiary scores have been calculated
    - We're ready to consolidate up the parent organization hierarchy
    """
    # Only trigger on status changes (not new periods)
    if not hasattr(instance, '_status_changed') or not instance._status_changed:
        return
    
    # Only consolidate when period is locked or submitted
    if instance.status not in [ReportingPeriod.Status.LOCKED, ReportingPeriod.Status.SUBMITTED]:
        return
    
    try:
        org_id = instance.organization.id
        period_id = instance.id
        
        logger.info(
            f"[ESG Signals] ReportingPeriod locked/submitted - triggering group consolidation "
            f"for organization {org_id}, period {period_id}"
        )
        
        with transaction.atomic():
            # Trigger group consolidation for this organization
            task = calculate_group_consolidation.delay(
                group_id=org_id,
                period_id=period_id
            )
            
            logger.debug(f"[ESG Signals] Queued group consolidation task: {task.id}")
            
    except Exception as e:
        logger.error(
            f"[ESG Signals] Error triggering consolidation on period close: {str(e)}",
            exc_info=True
        )
