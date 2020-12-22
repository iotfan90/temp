# -*- coding: utf-8 -*-
'''
Development settings

- Run in Debug mode
- Use console backend for emails
- Add Django Debug Toolbar
- Add django-extensions as app
'''
from datetime import timedelta

from .common import *  # noqa

# DEBUG
# ------------------------------------------------------------------------------
DEBUG = env.bool('DJANGO_DEBUG', default=True)
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG

# SECRET CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
# Note: This key only used for development and testing.
SECRET_KEY = env("DJANGO_SECRET_KEY", default='8_mz5vt-d^db=t*vbgs6^%h)1qjud)8w_k2au1_^0&k#_t2x!7')

# Mail settings
# ------------------------------------------------------------------------------
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
EMAIL_BACKEND = env('DJANGO_EMAIL_BACKEND',
                    default='django.core.mail.backends.console.EmailBackend')

# CACHING
# ------------------------------------------------------------------------------
CACHES = {
    'default': {
        'BACKEND': 'redis_cache.cache.RedisCache',
        'LOCATION': '127.0.0.1:6379',
        'TIMEOUT': 30 * 24 * 60 * 60,  # One month in seconds
        'OPTIONS': {
            'DB': 0,
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'SOCKET_TIMEOUT': 1,
            'CONNECTION_POOL_KWARGS': {'max_connections': 1},
        },
    }
}

# django-debug-toolbar
# ------------------------------------------------------------------------------
INTERNAL_IPS = ('127.0.0.1', '10.0.2.2',)

# django-extensions
# ------------------------------------------------------------------------------
INSTALLED_APPS += ('django_nose', )

# TESTING
# ------------------------------------------------------------------------------
# TEST_RUNNER = 'django.test.runner.DiscoverRunner'

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = [
    '--all-modules',
    '--verbosity=2'
]

ASSETS_DEBUG = 'merge'
ASSETS_AUTO_BUILD = True
# CELERY
# In development, all tasks will be executed locally by blocking until the task returns
CELERY_ALWAYS_EAGER = True
# END CELERY
# Your local stuff: Below this line define 3rd party library settings

# CELERYBEAT_SCHEDULE['run-campaigns']['schedule'] = timedelta(seconds=15)

# Import local (machine/developer specific) settings
try:
    from .local_overrides import *
except ImportError:
    # local settings is not mandatory
    pass

try:
    from .local import *
except ImportError:
    # local settings not mandatory
    pass

