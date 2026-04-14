"""Signals for group analytics - auto-recalculation on data changes."""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from compliance.models import FrameworkReadiness, ComplianceGapPriority, ComplianceRecommendation
from esg_scoring.models import ESGScore
from organizations.models import Organization
from .cache import invalidate_parent_cache, invalidate_group_cache


@receiver(post_save, sender=FrameworkReadiness)
def _framework_readiness_changed(sender, instance, created, **kwargs):
    """
    Invalidate group cache when framework readiness changes.
    
    Triggered when:
    - Readiness is calculated for an organization
    - Readiness scores are updated
    """
    org = instance.organization
    period = instance.reporting_period
    
    # Invalidate this org's cache (for individual view)
    invalidate_group_cache(org, period)
    
    # Invalidate parent's cached group aggregations
    invalidate_parent_cache(org, period)


@receiver(post_save, sender=ComplianceGapPriority)
def _compliance_gap_changed(sender, instance, created, **kwargs):
    """
    Invalidate group cache when compliance gaps change.
    """
    org = instance.organization
    
    # Invalidate group cache
    invalidate_group_cache(org)
    
    # Invalidate parent's cached group aggregations
    invalidate_parent_cache(org)


@receiver(post_delete, sender=ComplianceGapPriority)
def _compliance_gap_deleted(sender, instance, **kwargs):
    """
    Invalidate group cache when compliance gaps are deleted.
    """
    org = instance.organization
    
    invalidate_group_cache(org)
    invalidate_parent_cache(org)


@receiver(post_save, sender=ComplianceRecommendation)
def _compliance_recommendation_changed(sender, instance, created, **kwargs):
    """
    Invalidate group cache when recommendations change.
    """
    org = instance.organization
    
    invalidate_group_cache(org)
    invalidate_parent_cache(org)


@receiver(post_delete, sender=ComplianceRecommendation)
def _compliance_recommendation_deleted(sender, instance, **kwargs):
    """
    Invalidate group cache when recommendations are deleted.
    """
    org = instance.organization
    
    invalidate_group_cache(org)
    invalidate_parent_cache(org)


@receiver(post_save, sender=ESGScore)
def _esg_score_changed(sender, instance, created, **kwargs):
    """
    Invalidate group cache when ESG scores change.
    
    Triggered when:
    - ESG score is calculated for an organization
    - ESG scores are updated or recalculated
    """
    org = instance.organization
    period = instance.reporting_period
    
    # Invalidate this org's cache
    invalidate_group_cache(org, period)
    
    # Invalidate parent's cached group aggregations
    invalidate_parent_cache(org, period)


@receiver(post_save, sender=Organization)
def _organization_changed(sender, instance, created, **kwargs):
    """
    Invalidate group cache when organization changes.
    
    Handles:
    - Organization hierarchy changes (parent assignment)
    - Organization metadata changes that affect aggregations
    """
    # Invalidate parent's cache if organization's parent changed
    if instance.parent:
        invalidate_group_cache(instance.parent)
