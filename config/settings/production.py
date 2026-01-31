#=============================================================
# Production settings for Totalesg360-backend-API
#=============================================================
from pathlib import Path
from .utils import load_env_file, get_database_config

# Load production env before base so BASE reads the correct values
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_env_file(BASE_DIR, '.env')

from .base import *
import os

DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() in ("1", "true", "yes")
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()]

DATABASES = get_database_config(BASE_DIR / 'db.sqlite3')