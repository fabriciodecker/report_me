import os
from .settings import *

# Forçar produção
DEBUG = False

# Hosts permitidos
ALLOWED_HOSTS = ['*']  # Railway irá definir automaticamente

# Usar PostgreSQL se DATABASE_URL estiver disponível
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL)
    }
else:
    # Fallback para SQLite apenas se DATABASE_URL não estiver disponível
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Configurações de produção
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# Middleware para arquivos estáticos
if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# CORS para produção
CORS_ALLOW_ALL_ORIGINS = True  # Temporário para teste

# Configurações de segurança
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Logging
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