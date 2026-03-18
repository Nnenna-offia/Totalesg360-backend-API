from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.core import management
from django.apps import apps


@receiver(post_migrate)
def register_dashboard_periodic(sender, **kwargs):
    # Only run for the dashboard app or when migrations completed
    try:
        dashboard_app = apps.get_app_config('dashboard')
    except LookupError:
        return
    if sender.name != 'dashboard' and sender.name != dashboard_app.name:
        return
    try:
        # call the management command to register the periodic task
        management.call_command('register_dashboard_periodic')
    except Exception:
        # avoid failing migrations due to beat registration issues
        pass
