"""App configuration for Reports app."""
from django.apps import AppConfig


class ReportsConfig(AppConfig):
    """Configuration for Reports app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reports'
    
    def ready(self):
        """Load signals when app is ready."""
        import reports.signals  # noqa
