from django.apps import AppConfig


class GroupAnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'group_analytics'
    
    def ready(self):
        """Import signals when app is ready."""
        import group_analytics.signals  # noqa
