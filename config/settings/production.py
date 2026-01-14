#=============================================================
# Production settings for Totalesg360-backend-API
#=============================================================
from .base import *
import os
from .utils import load_env_file, get_database_config

load_env_file(BASE_DIR, '.env')

DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() in ("1", "true", "yes")
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()]

DATABASES = get_database_config(BASE_DIR / 'db.sqlite3')