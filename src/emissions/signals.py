from django.db.models.signals import post_save
from django.dispatch import receiver
from submissions.models.activity_submission import ActivitySubmission
from emissions.services.calculate_emission import calculate_and_store
from submissions.models.reporting_period import ReportingPeriod
from emissions.services.persist_indicators import persist_emission_indicators


@receiver(post_save, sender=ActivitySubmission)
def handle_activity_submission_saved(sender, instance, created, **kwargs):
    # Calculate emissions for new or updated submissions
    try:
        calculate_and_store(instance)
    except Exception:
        # swallow; calculation is best-effort here
        pass


@receiver(post_save, sender=ReportingPeriod)
def handle_reporting_period_locked(sender, instance, **kwargs):
    # When a reporting period is locked, persist emission-derived indicators
    try:
        if instance.status == ReportingPeriod.Status.LOCKED:
            # best-effort persistence; do not raise on failure
            try:
                persist_emission_indicators(instance.organization, instance, by_user=None, submit=True)
            except Exception:
                pass
    except Exception:
        pass
