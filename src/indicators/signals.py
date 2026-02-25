from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from organizations.models import OrganizationFramework
from indicators.services import schedule_sync_for_org


@receiver(post_save, sender=OrganizationFramework)
def _orgframework_saved(sender, instance, **kwargs):
    # schedule a sync for the organization when framework assignment changes
    org = instance.organization
    schedule_sync_for_org(org)


@receiver(post_delete, sender=OrganizationFramework)
def _orgframework_deleted(sender, instance, **kwargs):
    org = instance.organization
    schedule_sync_for_org(org)
