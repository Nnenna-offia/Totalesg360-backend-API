from .base import *
import os
from .utils import load_env_file, get_database_config

# load local overrides
load_env_file(BASE_DIR, '.env.local')

# local defaults
DEBUG = True
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()]

DATABASES = get_database_config(BASE_DIR / 'db.sqlite3')
