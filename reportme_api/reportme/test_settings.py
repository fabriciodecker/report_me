"""
Configurações específicas para testes do Django
"""

from .settings import *
import tempfile

# Database de teste em memória (SQLite)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Desabilitar migrações para acelerar testes
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None

# MIGRATION_MODULES = DisableMigrations()

# Configurações de email para testes
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Cache para testes
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Diretório temporário para arquivos de teste
MEDIA_ROOT = tempfile.mkdtemp()

# JWT com validade menor para testes
SIMPLE_JWT.update({
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(minutes=10),
})

# Logging mínimo durante testes
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'level': 'CRITICAL',
        },
    },
}

# Desabilitar debug durante testes
DEBUG = False

# Password hashers mais rápidos para testes
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Timezone para testes
USE_TZ = True
TIME_ZONE = 'UTC'