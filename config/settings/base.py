#==================================================================
# Django settings for the project.
# Base settings to be extended by other environment-specific settings.
#==================================================================

from pathlib import Path
import os
from .utils import load_env_file, get_database_config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load project-level .env (if present)
load_env_file(BASE_DIR, ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "your-default-secret-key")

DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() in ("1", "true", "yes")

ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()]
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True



# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    #third party apps
    'rest_framework',
    'corsheaders',
    'django_celery_beat',       # Celery Beat scheduler stored in DB
    'django_celery_results',    # optional: store task results in Django DB
    'django_redis',

    # local apps
    'common',
    'accounts',
    'organizations',
    'indicators',
    'roles',
    'submissions',
    # newly added apps
    'compliance',
    'targets',
    'dashboard',
    'activities',
    'emissions',
    'esg_scoring',
    'group_analytics',
    'reports',
]


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'accounts.auth.authentication.CookieJWTAuthentication',
    ],
    'EXCEPTION_HANDLER': 'common.drf.custom_exception_handler',
    # other DRF defaults can be set by the project as needed
}
# Custom user model
AUTH_USER_MODEL = 'accounts.User'

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'common.middleware.OrganizationContextMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = get_database_config(BASE_DIR / 'db.sqlite3')


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


STATIC_URL = 'static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.getenv('MEDIA_ROOT', str(BASE_DIR / 'media'))

# ---------------------------
# Redis / Cache configuration
# ---------------------------
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/1")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv("DJANGO_CACHE_LOCATION", REDIS_URL),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

# Dashboard snapshot retention (days)
DASHBOARD_SNAPSHOT_RETENTION_DAYS = int(os.getenv("DASHBOARD_SNAPSHOT_RETENTION_DAYS", 90))


# ---------------------------
# Celery configuration
# ---------------------------
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# Use django-celery-beat database scheduler if installed
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers.DatabaseScheduler"

CELERY_BROKER_TRANSPORT_OPTIONS = {
    "visibility_timeout": int(os.getenv("CELERY_VISIBILITY_TIMEOUT", 3600)),
}

# Email configuration (from environment)
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() in ("1", "true", "yes")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)

# OTP defaults
OTP_TTL_SECONDS = int(os.getenv("OTP_TTL_SECONDS", 3600))
OTP_LENGTH = int(os.getenv("OTP_LENGTH", 6))
OTP_MAX_REQUESTS_PER_HOUR = int(os.getenv("OTP_MAX_REQUESTS_PER_HOUR", 6))
OTP_MAX_RESEND_PER_HOUR = int(os.getenv("OTP_MAX_RESEND_PER_HOUR", 5))

# Problem document base URL for RFC7807 `type` fields (configurable via .env)
PROBLEM_BASE_URL = os.getenv("PROBLEM_BASE_URL", "https://totalesg360.com/probs")

# Run tasks in the real worker by default, even in development.
# Override with CELERY_TASK_ALWAYS_EAGER=1 only when you explicitly want inline execution.
CELERY_TASK_ALWAYS_EAGER = os.getenv("CELERY_TASK_ALWAYS_EAGER", "0").lower() in ("1", "true", "yes")
CELERY_TASK_EAGER_PROPAGATES = os.getenv("CELERY_TASK_EAGER_PROPAGATES", "1").lower() in ("1", "true", "yes")

# ---------------------------
# JWT Authentication Configuration
# ---------------------------
JWT_SECRET = os.getenv("JWT_SECRET", SECRET_KEY)
JWT_ALGORITHM = "HS256"
JWT_ISS = "totalesg360"

# Token lifetimes
JWT_ACCESS_LIFETIME_SECONDS = int(os.getenv("JWT_ACCESS_LIFETIME_SECONDS", 300))  # 5 minutes
JWT_REFRESH_LIFETIME_SECONDS = int(os.getenv("JWT_REFRESH_LIFETIME_SECONDS", 7 * 24 * 3600))  # 7 days

# Cookie names
ACCESS_COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"

# CSRF Configuration (for cookie-based auth)
CSRF_COOKIE_SECURE = not DEBUG  # True in production
CSRF_COOKIE_HTTPONLY = False  # Must be False so frontend can read it
CSRF_COOKIE_SAMESITE = "None" if not DEBUG else "Lax"  # None in production, Lax in dev
CSRF_COOKIE_NAME = "csrftoken"
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if origin.strip()]

# CORS configuration - allow frontend origins to access API and send credentials
# Do NOT set CORS_ALLOW_ALL_ORIGINS = True when using credentials; instead whitelist origins.
CORS_ALLOWED_ORIGINS = [
    origin.strip() for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if origin.strip()
]

CORS_ALLOW_CREDENTIALS = True

from corsheaders.defaults import default_headers

CORS_ALLOW_HEADERS = list(default_headers) + [
    'X-CSRFToken',
     "X-ORG-ID",
]

# Expose the CSRF header to browsers so frontends on other origins can read it
CORS_EXPOSE_HEADERS = [
    'X-CSRFToken',
]

# Session cookie security
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "None" if not DEBUG else "Lax"  # None in production, Lax in dev

# ---------------------------
# JWT Token Cookies Configuration (for Cross-Origin Requests)
# ---------------------------
# Access token cookie settings (for cross-origin auth)
ACCESS_COOKIE_SECURE = not DEBUG  # True in production, False in dev
ACCESS_COOKIE_SAMESITE = "None" if not DEBUG else "Lax"
ACCESS_COOKIE_HTTPONLY = True

# Refresh token cookie settings (for cross-origin token refresh)
REFRESH_COOKIE_SECURE = not DEBUG  # True in production, False in dev
REFRESH_COOKIE_SAMESITE = "None" if not DEBUG else "Lax"
REFRESH_COOKIE_HTTPONLY = True

# ---------------------------
# Logging Configuration
# ---------------------------
# Ensure logs directory exists before configuring logging
import logging
import logging.handlers
import tempfile

# Create logs directory with absolute path - with fallback and permission check
LOG_DIR = os.path.join(str(BASE_DIR), "logs")
CAN_WRITE_LOGS = False

try:
    os.makedirs(LOG_DIR, exist_ok=True)
    # Test if we can actually write to the directory
    test_file = os.path.join(LOG_DIR, ".write_test")
    with open(test_file, "w") as f:
        f.write("test")
    os.remove(test_file)
    CAN_WRITE_LOGS = True
except (OSError, PermissionError, IOError):
    # Fallback to temp directory if primary path is not writable
    try:
        LOG_DIR = os.path.expanduser("~/totalesg_logs")
        os.makedirs(LOG_DIR, exist_ok=True)
        test_file = os.path.join(LOG_DIR, ".write_test")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        CAN_WRITE_LOGS = True
    except (OSError, PermissionError, IOError):
        # Last resort: use system temp
        LOG_DIR = tempfile.gettempdir()
        CAN_WRITE_LOGS = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} {name} {module}.{funcName}:{lineno} - {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "[{levelname}] {name} - {message}",
            "style": "{",
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
        } if os.getenv("USE_JSON_LOGS", "").lower() in ("1", "true", "yes") else {
            "format": "[{levelname}] {asctime} {name} - {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "handlers": {
        "console": {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "class": "logging.StreamHandler",
            "formatter": "verbose" if DEBUG else "json",
        },
        **(
            {
                "file": {
                    "level": "INFO",
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": os.path.join(LOG_DIR, "totalesg.log"),
                    "maxBytes": 10 * 1024 * 1024,  # 10MB
                    "backupCount": 5,
                    "formatter": "verbose",
                    "delay": True,
                },
                "error_file": {
                    "level": "ERROR",
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": os.path.join(LOG_DIR, "errors.log"),
                    "maxBytes": 10 * 1024 * 1024,  # 10MB
                    "backupCount": 5,
                    "formatter": "verbose",
                    "delay": True,
                },
            }
            if CAN_WRITE_LOGS
            else {}
        ),
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": (["console", "error_file"] if CAN_WRITE_LOGS else ["console"]),
            "level": "WARNING",
            "propagate": False,
        },
        "django.server": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"] if os.getenv("LOG_SQL", "").lower() in ("1", "true", "yes") else ["null"],
            "level": "DEBUG",
            "propagate": False,
        },
        # Application loggers
        "accounts": {
            "handlers": (["console", "file"] if CAN_WRITE_LOGS else ["console"]),
            "level": os.getenv("APP_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "organizations": {
            "handlers": (["console", "file"] if CAN_WRITE_LOGS else ["console"]),
            "level": os.getenv("APP_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "roles": {
            "handlers": (["console", "file"] if CAN_WRITE_LOGS else ["console"]),
            "level": os.getenv("APP_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "common": {
            "handlers": (["console", "file"] if CAN_WRITE_LOGS else ["console"]),
            "level": os.getenv("APP_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        # Namespace loggers for structured logging
        "services": {
            "handlers": (["console", "file"] if CAN_WRITE_LOGS else ["console"]),
            "level": os.getenv("APP_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "api": {
            "handlers": (["console", "file"] if CAN_WRITE_LOGS else ["console"]),
            "level": os.getenv("APP_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "tasks": {
            "handlers": (["console", "file"] if CAN_WRITE_LOGS else ["console"]),
            "level": os.getenv("APP_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        # Celery
        "celery": {
            "handlers": (["console", "file"] if CAN_WRITE_LOGS else ["console"]),
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": (["console", "file", "error_file"] if CAN_WRITE_LOGS else ["console"]),
        "level": os.getenv("ROOT_LOG_LEVEL", "INFO"),
    },
}
