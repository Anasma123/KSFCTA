"""
Django settings for ksfcta_project project.
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-inlh)lgp5vm(_^x1*g0uj#&gp3y)5yyaqx%d&wa!wzp)p!njjp'

DEBUG = True

ALLOWED_HOSTS = ['.vercel.app', 'now.sh', '127.0.0.1', 'localhost', '*']

CSRF_TRUSTED_ORIGINS = [
    'https://ksfcta.vercel.app',
    'https://*.vercel.app',
    'https://*.now.sh',
    'http://127.0.0.1:8000',
    'http://localhost:8000',
    'http://127.0.0.1',
    'http://localhost',
]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Enforce secure cookies in production (Vercel is HTTPS)
if os.environ.get('VERCEL'):
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    # Ensure CSRF works across possible Vercel proxy changes
    CSRF_COOKIE_SAMESITE = 'None'
    SESSION_COOKIE_SAMESITE = 'None'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'membership',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ksfcta_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
            ],
        },
    },
]

WSGI_APPLICATION = 'ksfcta_project.wsgi.application'

import dj_database_url

NEON_DB_URL = "postgresql://neondb_owner:npg_Kho0nTjGO2pc@ep-holy-smoke-b4mxtrxv-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require"
DATABASES = {
    'default': dj_database_url.config(
        default=NEON_DB_URL,
        conn_max_age=600,
        conn_health_checks=True,
    )
}

if os.environ.get('VERCEL'):
    MEDIA_ROOT = Path('/tmp/media')
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
else:
    MEDIA_ROOT = BASE_DIR / 'media'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 4}
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/admin-portal/'
LOGOUT_REDIRECT_URL = '/login/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Use default database-backed sessions (Now supported securely by Neon Postgres)
# SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

# Disable all server-side caching (Vercel edge cache prevention)
CACHE_MIDDLEWARE_SECONDS = 0
