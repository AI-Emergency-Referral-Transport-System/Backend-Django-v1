from .base import *


DEBUG = True
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", ["localhost", "127.0.0.1", "0.0.0.0"])





# Override the database for local development to skip GDAL requirements
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Use sqlite3 for the fastest fix
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}