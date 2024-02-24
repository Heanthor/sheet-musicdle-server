"""
Django settings for sheet_musicle_server project.

Generated by 'django-admin startproject' using Django 4.2.6.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
ENV = os.getenv("SM_ENV", "dev")
print("Starting with env: " + ENV)
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-)q$w3sa%_6u$(f5p%*gknca44qz09&!23w!qn)j@#460^(_pf("
if ENV == "prod":
    SECRET_KEY = os.getenv("SM_SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
if ENV == "prod":
    DEBUG = False

LOG_QUERIES = False

ALLOWED_HOSTS = []
if ENV == "prod":
    ALLOWED_HOSTS = ["sheet-musicle.com", "api.sheet-musicle.com"]
    CORS_ALLOWED_ORIGINS = [
        "https://sheet-musicle.com",
        "https://api.sheet-musicle.com",
    ]
else:
    CORS_ALLOW_ALL_ORIGINS = True
    DJANGO_CPROFILE_MIDDLEWARE_REQUIRE_STAFF = False

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Application definition

INSTALLED_APPS = [
    "sheet_api.apps.SheetApiConfig",
    "sheet_api.apps.MyAdminConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "django_cprofile_middleware.middleware.ProfilerMiddleware",
]


ROOT_URLCONF = "sheet_musicle_server.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
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

WSGI_APPLICATION = "sheet_musicle_server.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

db_dict = {
    "ENGINE": "django.db.backends.postgresql",
    "OPTIONS": {
        "service": "sheet_musicle",
        "passfile": "/Users/reedtrevelyan/.pgpass",
    },
}

if ENV == "prod":
    db_dict = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "sheet_musicle",
        "USER": os.getenv("SM_DB_USER"),
        "PASSWORD": os.getenv("SM_DB_PASS"),
        "HOST": os.getenv("SM_DB_HOST"),
        "PORT": 5432,
    }

DATABASES = {
    "default": db_dict,
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

if LOG_QUERIES:
    LOGGING = {
        "version": 1,
        "filters": {
            "require_debug_true": {
                "()": "django.utils.log.RequireDebugTrue",
            }
        },
        "handlers": {
            "console": {
                "level": "DEBUG",
                "filters": ["require_debug_true"],
                "class": "logging.StreamHandler",
            }
        },
        "loggers": {
            "django.db.backends": {
                "level": "DEBUG",
                "handlers": ["console"],
            }
        },
    }

if ENV == "prod":
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
            },
        },
        "root": {
            "handlers": ["console"],
            "level": "WARNING",
        },
    }

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "EST"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Application settings
if ENV == "prod":
    # if true, do not allow puzzles to be retrieved with dates greater than the current date
    HIDE_NEW_PUZZLES = True
    SKIP_USAGE_EVENT_WRITE = False
else:
    HIDE_NEW_PUZZLES = False
    SKIP_USAGE_EVENT_WRITE = True
