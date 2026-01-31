#=================================================================
# Local settings for Django project
# Overrides base settings for local development
#=================================================================

from pathlib import Path
from .utils import load_env_file, get_database_config

# Load local overrides before importing base so settings pick them up
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_env_file(BASE_DIR, '.env.local')

from .base import *
import os

# local defaults (can be overridden from .env.local)
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() in ("1", "true", "yes")
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()]

# Database (driven by env vars via get_database_config)
DATABASES = get_database_config(BASE_DIR / 'db.sqlite3')
