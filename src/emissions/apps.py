from django.apps import AppConfig


class EmissionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'emissions'
    verbose_name = 'Emissions'
    
    def ready(self):
        # import signals so they are registered
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
