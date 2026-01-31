from __future__ import annotations
import os
from celery import Celery
from django.conf import settings

# Ensure the Django settings module is set. Prefer external env var if provided.
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    os.environ.get("DJANGO_SETTINGS_MODULE", "config.settings.local"),
)

app = Celery("config")

# Read configuration from Django settings, using the `CELERY_` namespace.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Autodiscover tasks in installed apps (looks for tasks.py)
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Celery debug task running: {self.request!r}")
