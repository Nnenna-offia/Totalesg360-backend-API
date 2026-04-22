from django.db.models.signals import post_save
from django.dispatch import receiver

from organizations.models import Organization, OrganizationESGSettings
from organizations.services.esg_settings import ensure_reporting_period


@receiver(post_save, sender=Organization)
def create_esg_settings(sender, instance, created, **kwargs):
    if not created:
        return

    OrganizationESGSettings.objects.get_or_create(
        organization=instance,
        defaults={"reporting_level": instance.entity_type or Organization.EntityType.SUBSIDIARY},
    )


@receiver(post_save, sender=OrganizationESGSettings)
def ensure_reporting_period_for_settings(sender, instance, **kwargs):
    ensure_reporting_period(instance)