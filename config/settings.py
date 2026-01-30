from pathlib import Path
import os
import cloudinary
import cloudinary.uploader
import cloudinary.api
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qsl


load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
# NOTE: Custom 404 and 500 error pages are only shown when DEBUG=False
# Set DEBUG=False in production environment variables (.env file)
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')


# Application definition

INSTALLED_APPS = [
    'chat',
    'cloudinary_storage',
    'cloudinary',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
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
    'chat.middleware.RateLimitMiddleware',  # Rate limiting for all requests
    'chat.middleware.APIRateLimitMiddleware',  # Additional rate limiting for AI API calls
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'config.context_processors.admin_url',  # Add admin URL to context
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database configuration with safe handling for build phase
# During Render build, DATABASE_URL may not be available
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    tmpPostgres = urlparse(DATABASE_URL)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': tmpPostgres.path.replace('/', ''),
            'USER': tmpPostgres.username,
            'PASSWORD': tmpPostgres.password,
            'HOST': tmpPostgres.hostname,
            'PORT': 5432,
            'OPTIONS': dict(parse_qsl(tmpPostgres.query)),
            'CONN_MAX_AGE': 0,  # Let Neon's PgBouncer handle connection pooling
            'DISABLE_SERVER_SIDE_CURSORS': True,
            'CONN_HEALTH_CHECKS': False,
        }
    }
else:
    # Fallback for build phase when DATABASE_URL is not set
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Explicitly set staticfiles finders
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- FIX FOR PROJECT IDX / CLOUD ENVIRONMENTS ---
# Trust requests from Google's cloud workstations
CSRF_TRUSTED_ORIGINS = [
    'https://*.cloudworkstations.dev',
    'https://*.idx.dev', 
    'http://127.0.0.1:8000',
    'https://*.onrender.com',
]

# Load keys from .env (Security Best Practice)
# We will add these to your .env file in the next step
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.getenv('CLOUDINARY_API_KEY'),
    'API_SECRET': os.getenv('CLOUDINARY_API_SECRET'),
}

# ... keys are above this ...
# settings.py

STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        # ✅ SAFE BACKEND: (CompressedStaticFilesStorage)
        # This compresses files but DOES NOT crash on missing links
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# ✅ MATCHING SAFE BACKEND
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

# 3. ADD THIS LINE (The Fix from the Docs)
# This tells WhiteNoise: "If you find a missing file reference (like admin/css/widgets.css),
# don't crash the build. Just ignore it and keep going."
WHITENOISE_MANIFEST_STRICT = False

# --- AUTH REDIRECTS ---
LOGIN_REDIRECT_URL = '/chat/'  # Go to chat page after login
LOGOUT_REDIRECT_URL = '/accounts/login/' # Go to login page after logout

# --- LOGGING CONFIGURATION ---
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'debug.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'chat': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# --- FILE UPLOAD SETTINGS ---
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB

# --- CACHE CONFIGURATION (Required for Rate Limiting) ---
# Production (Render): Use DatabaseCache for multi-worker support (persists across dyno sleep)
# Redis: If Redis is available, use it instead
REDIS_URL = os.getenv('REDIS_URL', None)

if REDIS_URL:
    # PRODUCTION with Redis: Redis cache for multi-worker rate limiting
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 50,
                    'retry_on_timeout': True,
                },
                'SOCKET_CONNECT_TIMEOUT': 5,
                'SOCKET_TIMEOUT': 5,
            },
            'KEY_PREFIX': 'nexus',
            'TIMEOUT': 300,
        }
    }
else:
    # PRODUCTION (Render free tier): Use DatabaseCache (shared across 4 workers, persists on sleep)
    # Accurate rate limits across all workers + persistent quotas even after dyno sleep
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'django_cache_table',
            'OPTIONS': {
                'MAX_ENTRIES': 10000,
            }
        }
    }