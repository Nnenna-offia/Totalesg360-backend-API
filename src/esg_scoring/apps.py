"""ESG Scoring App Configuration."""
from django.apps import AppConfig


class EsgScoringConfig(AppConfig):
    """Configuration for ESG Scoring App."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'esg_scoring'
    verbose_name = 'ESG Scoring Engine'
    
    def ready(self):
        """Register signal handlers when app is ready."""
        import esg_scoring.signals  # noqa
