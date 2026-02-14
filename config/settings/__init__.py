"""Settings package initializer.

Ensure `src/` is on `sys.path` so local Django apps (e.g. `common`, `accounts`)
are importable when processes start without using `manage.py` (Celery,
gunicorn, etc.).
"""
from pathlib import Path
import sys

# Add repo/src to import path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
src_path = str(BASE_DIR / "src")
if src_path not in sys.path:
	sys.path.insert(0, src_path)

from .base import *
from .celery import app as celery_app

__all__ = ("celery_app",)

