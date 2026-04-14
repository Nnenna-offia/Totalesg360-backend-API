"""Signals for Reports app - regenerate reports on data changes."""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from esg_scoring.models import ESGScore
from compliance.models import FrameworkReadiness, ComplianceGapPriority, ComplianceRecommendation
from reports.services import regenerate_all_reports


@receiver(post_save, sender=ESGScore)
def _esg_score_changed(sender, instance, created, **kwargs):
    """Regenerate reports when ESG score changes."""
    regenerate_all_reports(instance.organization)


@receiver(post_save, sender=FrameworkReadiness)
def _framework_readiness_changed(sender, instance, created, **kwargs):
    """Regenerate reports when framework readiness changes."""
    regenerate_all_reports(instance.organization)


@receiver(post_save, sender=ComplianceGapPriority)
def _compliance_gap_changed(sender, instance, created, **kwargs):
    """Regenerate reports when compliance gap changes."""
    regenerate_all_reports(instance.organization)


@receiver(post_delete, sender=ComplianceGapPriority)
def _compliance_gap_deleted(sender, instance, **kwargs):
    """Regenerate reports when compliance gap is deleted."""
    regenerate_all_reports(instance.organization)


@receiver(post_save, sender=ComplianceRecommendation)
def _compliance_recommendation_changed(sender, instance, created, **kwargs):
    """Regenerate reports when recommendation changes."""
    regenerate_all_reports(instance.organization)


@receiver(post_delete, sender=ComplianceRecommendation)
def _compliance_recommendation_deleted(sender, instance, **kwargs):
    """Regenerate reports when recommendation is deleted."""
    regenerate_all_reports(instance.organization)
