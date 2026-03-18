from django.apps import AppConfig


class DashboardConfig(AppConfig):
    name = 'dashboard'
    verbose_name = 'Dashboard / Analytics'

    def ready(self):
        # import signals to register periodic task after migrations
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
from django.apps import AppConfig


class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard'
    verbose_name = 'Dashboard & Analytics'
