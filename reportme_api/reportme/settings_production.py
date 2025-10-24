import os
from .settings import *

# Override settings for production
DEBUG = config('DEBUG', default=False, cast=bool)

# Hosts permitidos - incluindo domínios das principais plataformas
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS', 
    default='localhost,127.0.0.1,.railway.app,.onrender.com,.herokuapp.com,.ondigitalocean.app',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# Database para produção
# Se DATABASE_URL estiver definida (Railway, Heroku), usa PostgreSQL
# Senão, mantém SQLite para desenvolvimento/teste
DATABASE_URL = config('DATABASE_URL', default=None)
if DATABASE_URL:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL)
    }

# Static files para produção
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# Middleware para servir arquivos estáticos (opcional - só se precisar)
if 'whitenoise' not in [app for app in INSTALLED_APPS]:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Security settings for production
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 3600
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# CORS settings - mais flexível
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Só permite tudo em desenvolvimento
if not DEBUG:
    # Em produção, configure os domínios específicos
    frontend_url = config('FRONTEND_URL', default='')
    if frontend_url:
        CORS_ALLOWED_ORIGINS = [
            frontend_url,
            frontend_url.replace('https://', 'http://'),  # fallback
        ]

# Configurações de cache (opcional para performance)
if not DEBUG:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

# Logging para produção
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}