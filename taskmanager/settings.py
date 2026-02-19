"""
Django settings for taskmanager project.
Multi-Organization Task Management System
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-(q*b5v!00vvg%(5mkiu7ny%q6@-q8!k-5ox^3fxi(lws8m%xl%"

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Project apps
    "core",
    "projects",
    "tasks",
    "issues",
    "templates_lib",
    "reports",
    "forms_app",
    "notifications",
    "ai_engine",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.LoginRequiredMiddleware",
]

ROOT_URLCONF = "taskmanager.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.global_context",
            ],
        },
    },
]

WSGI_APPLICATION = "taskmanager.wsgi.application"

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Session settings
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 86400
SESSION_SAVE_EVERY_REQUEST = True

# External Login API
STYLEHR_LOGIN_API = "https://stylehr.in/api/login/"

# Login URL
LOGIN_URL = "/login/"

# Default auto field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ============================================================
# REDIS CACHING
# ============================================================
# Set USE_REDIS=True when Redis is available (brew services start redis)
USE_REDIS = os.environ.get("USE_REDIS", "false").lower() == "true"

if USE_REDIS:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/1"),
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
            "TIMEOUT": 300,  # 5 minutes default
        }
    }
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
    SESSION_CACHE_ALIAS = "default"
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "TIMEOUT": 300,
        }
    }

# Cache timeouts (seconds)
CACHE_TTL_DASHBOARD = 120   # 2 minutes
CACHE_TTL_REPORTS = 600     # 10 minutes
CACHE_TTL_TEMPLATES = 1800  # 30 minutes

# ============================================================
# CELERY CONFIGURATION
# ============================================================
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300  # 5 minutes

# Celery Beat schedule (periodic tasks)
from datetime import timedelta
CELERY_BEAT_SCHEDULE = {
    "check-overdue-tasks": {
        "task": "notifications.tasks.check_overdue_tasks",
        "schedule": timedelta(hours=1),
    },
    "send-smart-reminders": {
        "task": "notifications.tasks.send_smart_reminders",
        "schedule": timedelta(hours=4),
    },
    "refresh-report-cache": {
        "task": "reports.tasks.refresh_report_cache",
        "schedule": timedelta(hours=6),
    },
    "check-recurring-tasks": {
        "task": "tasks.celery_tasks.process_recurring_tasks",
        "schedule": timedelta(hours=1),
    },
}

# ============================================================
# PAGINATION
# ============================================================
DEFAULT_PAGE_SIZE = 10
PAGE_SIZE_OPTIONS = [10, 25, 50, 100]
