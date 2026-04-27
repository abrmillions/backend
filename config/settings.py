
from pathlib import Path
import os
from decouple import config
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None
from .patches import apply_patches

BASE_DIR = Path(__file__).resolve().parent.parent
apply_patches()

if load_dotenv:
    try:
        load_dotenv(str(BASE_DIR / ".env"))
    except Exception:
        pass

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or os.environ.get("SECRET_KEY") or "change-me-in-production"

DEBUG = (os.environ.get("DJANGO_DEBUG") or os.environ.get("DEBUG") or "1") == "1"

_hosts = os.environ.get("DJANGO_ALLOWED_HOSTS") or os.environ.get("ALLOWED_HOSTS") or ""
ALLOWED_HOSTS = _hosts.split(",") if _hosts else []

# CSRF trusted origins: accept both DJANGO_* and unprefixed envs
_csrf = os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS") or os.environ.get("CSRF_TRUSTED_ORIGINS") or ""
CSRF_TRUSTED_ORIGINS = [o for o in _csrf.split(",") if o] if _csrf else []

# In development, always allow common origins and hosts
if DEBUG:
    ALLOWED_HOSTS = ["*"]
    if not CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS = [
            "https://digital-licensing.vercel.app",
            "https://backend-8zt1.onrender.com",
         
           
        ]
    # Ensure local dev also trusts same-origin requests
    CSRF_TRUSTED_ORIGINS += ["https://backend-8zt1.onrender.com"]

# Safe defaults for Render if not explicitly configured
if not DEBUG:
    if not ALLOWED_HOSTS:
        ALLOWED_HOSTS = [
            ".onrender.com",
          
            "[::1]",
        ]
    if not CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS = [
            "https://backend-8zt1.onrender.com",
            "https://digital-licensing.vercel.app",
        ]
INSTALLED_APPS = [
  "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "cloudinary_storage",
    "django.contrib.staticfiles",
    "cloudinary",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "users",
    "licenses",
    "vehicles",
    "partnerships",
    "payments",
    "applications",
    "documents",
    "systemsettings",
    "contact",
    "companies.apps.CompaniesConfig",
    "license_history.apps.LicenseHistoryConfig",
]

# Use custom user model
AUTH_USER_MODEL = os.environ.get("AUTH_USER_MODEL", "users.CustomUser")

# Use WhiteNoise to serve static files on Render
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "config.middleware.MaintenanceModeMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

import dj_database_url

# Database: Use DATABASE_URL if available, otherwise check individual DB_* variables, fallback to SQLite
db_url = os.environ.get("DATABASE_URL")
if not db_url and os.environ.get("DB_NAME"):
    # Build URL from individual variables
    engine = os.environ.get("DB_ENGINE", "postgresql")
    if "postgresql" in engine:
        scheme = "postgres"
    elif "mysql" in engine:
        scheme = "mysql"
    elif "sqlite" in engine:
        scheme = "sqlite"
    else:
        scheme = "postgres"
    
    user = os.environ.get("DB_USER", "")
    password = os.environ.get("DB_PASSWORD", "")
    host = os.environ.get("DB_HOST", "localhost")
    port = os.environ.get("DB_PORT", "5432")
    name = os.environ.get("DB_NAME", "")
    
    db_url = f"{scheme}://{user}:{password}@{host}:{port}/{name}"

DATABASES = {
    "default": dj_database_url.config(
        default=db_url or f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=0,
        conn_health_checks=False,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# Ensure STATIC_ROOT exists during initialization
if not STATIC_ROOT.exists():
    try:
        STATIC_ROOT.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Remove the manual insertion of WhiteNoiseMiddleware since it's already in MIDDLEWARE
# try:
#     if not DEBUG and STATIC_ROOT.exists():
#         MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
# except Exception:
#     pass

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Cloudinary Configuration for Production
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
}

if not DEBUG:
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Ensure MEDIA_ROOT exists during initialization
if not MEDIA_ROOT.exists():
    try:
        MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

# REST framework and JWT
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ),
}

from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.environ.get("JWT_ACCESS_MINUTES", "60"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.environ.get("JWT_REFRESH_DAYS", "1"))),
    "ROTATE_REFRESH_TOKENS": False,
}

# CORS
CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",") if os.environ.get("CORS_ALLOWED_ORIGINS") else []
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
APPEND_SLASH = True
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.vercel\.app$",
]

# In development, allow the frontend origin by default
if DEBUG and not CORS_ALLOW_ALL_ORIGINS and not CORS_ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS = [
        "https://digital-licensing.vercel.app",
        "https://backend-8zt1.onrender.com",
    ]

# In production, default to known frontend origin if not configured
ADMIN_IP_WHITELIST = [ip.strip() for ip in (os.environ.get("ADMIN_IP_WHITELIST") or "").split(",") if ip.strip()]
if not DEBUG and not CORS_ALLOW_ALL_ORIGINS and not CORS_ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS = [
        "https://digital-licensing.vercel.app",
    ]

# QR token max age (seconds). Default 7 days; can be overridden via env var.
# Shorter default reduces exposure if tokens are leaked. Override with `QR_TOKEN_MAX_AGE_SECONDS` env var.
QR_TOKEN_MAX_AGE_SECONDS = int(os.environ.get('QR_TOKEN_MAX_AGE_SECONDS', str(60 * 60 * 24 * 7)))

# Ensure correct scheme on Render behind proxy
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Chapa Payment Integration
FRONTEND_URL = config("FRONTEND_URL", default="https://digital-licensing.vercel.app")

# Logging Configuration
LOGS_DIR = BASE_DIR / "logs"
if not LOGS_DIR.exists():
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

# Determine log handler based on environment and OS
if DEBUG and os.name == 'nt':
    # On Windows during development, use standard FileHandler to avoid PermissionError
    # when Django's autoreloader starts multiple processes.
    file_handler_class = "logging.FileHandler"
    file_handler_kwargs = {}
else:
    # In production or non-Windows, use TimedRotatingFileHandler for daily logs
    file_handler_class = "logging.handlers.TimedRotatingFileHandler"
    file_handler_kwargs = {
        "when": "midnight",
        "interval": 1,
        "backupCount": 7,
    }

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": file_handler_class,
            "filename": LOGS_DIR / "clms_backend.log",
            "formatter": "verbose",
            "encoding": "utf-8",
            **file_handler_kwargs,
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "applications": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "documents": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
