import glob
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-fw@*-olpidf^0ooir34+lbq^hdn-w%q$00-!*)5o5r+lpkd63#",
)
DEBUG = os.getenv("DJANGO_DEBUG", "True").strip().lower() == "true"
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",")
    if host.strip()
]

# --- 1. GIS / GEODJANGO CONFIG ---
OSGEO4W_BIN = Path(os.environ.get("OSGEO4W_BIN", r"C:\OSGeo4W\bin"))
gdal_files = glob.glob(str(OSGEO4W_BIN / "gdal*.dll")) if OSGEO4W_BIN.exists() else []
gis_override = os.environ.get("GIS_ENABLED", "").lower()
if gis_override in {"1", "true", "yes", "on"}:
    GIS_ENABLED = True
elif gis_override in {"0", "false", "no", "off"}:
    GIS_ENABLED = False
else:
    GIS_ENABLED = os.name != "nt" or bool(gdal_files)

if GIS_ENABLED:
    if os.name == "nt":
        if gdal_files:
            os.environ["PATH"] = str(OSGEO4W_BIN) + os.pathsep + os.environ["PATH"]
            GDAL_LIBRARY_PATH = gdal_files[0]
        geos_library = OSGEO4W_BIN / "geos_c.dll"
        if geos_library.exists():
            GEOS_LIBRARY_PATH = str(geos_library)
    else:
        gdal_library_path = os.environ.get("GDAL_LIBRARY_PATH", "")
        geos_library_path = os.environ.get("GEOS_LIBRARY_PATH", "")
        if gdal_library_path:
            GDAL_LIBRARY_PATH = gdal_library_path
        if geos_library_path:
            GEOS_LIBRARY_PATH = geos_library_path
else:
    print(r"WARNING: GIS features are disabled because GDAL was not found.")

# --- 2. INSTALLED APPS ---
INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "channels",
    "accounts",
    "common",
    "system_admin",
]

if GIS_ENABLED:
    INSTALLED_APPS.insert(4, "django.contrib.gis")

if GIS_ENABLED:
    INSTALLED_APPS += [
        "tracking",
        "emergencies",
        "hospitals",
        "ambulances",
        "ai",
    ]

# --- 3. AUTH & USER CONFIG ---
AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# --- 4. DATABASE CONFIG ---
use_postgres_raw = os.environ.get("USE_POSTGRES", "")
if use_postgres_raw:
    USE_POSTGRES = use_postgres_raw.lower() in {"1", "true", "yes", "on"}
else:
    USE_POSTGRES = bool(os.environ.get("POSTGRES_DB"))

if USE_POSTGRES:
    default_engine = "django.contrib.gis.db.backends.postgis" if GIS_ENABLED else "django.db.backends.postgresql"
    DATABASES = {
        "default": {
            "ENGINE": os.environ.get("POSTGRES_ENGINE", default_engine),
            "NAME": os.environ.get("POSTGRES_DB", "herd_db"),
            "USER": os.environ.get("POSTGRES_USER", "postgres"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
            "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# --- 5. CHANNELS / ASGI ---
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")],
        },
    },
}

# --- 6. OTP DELIVERY CONFIG ---
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "no-reply@ai-emergency.local")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "25"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "").lower() in {"1", "true", "yes", "on"}
EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "").lower() in {"1", "true", "yes", "on"}

# --- 7. MIDDLEWARE ---
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

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
LANGUAGE_CODE = "en-us"
TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
