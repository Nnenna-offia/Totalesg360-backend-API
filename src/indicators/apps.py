from django.apps import AppConfig

class IndicatorsConfig(AppConfig):
	default_auto_field = 'django.db.models.BigAutoField'
	name = 'indicators'
	verbose_name = 'Indicators'
    
	def ready(self):
		# register signals
		try:
			from . import signals  # noqa: F401
		except Exception:
			pass
