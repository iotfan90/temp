# -*- coding: utf-8 -*-
'''
Production Configurations

- Use djangosecure
- Use Amazon's S3 for storing static files and uploaded media
- Use mailgun to send emails
- Use Redis on Heroku


'''
from __future__ import absolute_import, unicode_literals

import datetime
from boto.s3.connection import OrdinaryCallingFormat
from django.utils import six
import logging


from .common import *  # noqa

# SECRET CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
# Raises ImproperlyConfigured ("exception if DJANGO_SECRET_KEY not in os.environ
SECRET_KEY = env("DJANGO_SECRET_KEY")

# This ensures that Django will be able to detect a secure connection
# properly on Heroku.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# django-secure
# ------------------------------------------------------------------------------
INSTALLED_APPS += ("djangosecure", )

SECURITY_MIDDLEWARE = (
    'djangosecure.middleware.SecurityMiddleware',
)


# Make sure djangosecure.middleware.SecurityMiddleware is listed first
MIDDLEWARE_CLASSES = SECURITY_MIDDLEWARE + MIDDLEWARE_CLASSES

# set this to 60 seconds and then to 518400 when you can prove it works
SECURE_HSTS_SECONDS = 60
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True)
SECURE_FRAME_DENY = env.bool("DJANGO_SECURE_FRAME_DENY", default=True)
SECURE_CONTENT_TYPE_NOSNIFF = env.bool(
    "DJANGO_SECURE_CONTENT_TYPE_NOSNIFF", default=True)
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True
# SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=False)

# SITE CONFIGURATION
# ------------------------------------------------------------------------------
# Hosts/domain names that are valid for this site
# See https://docs.djangoproject.com/en/1.6/ref/settings/#allowed-hosts
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['.mobovidata.com'])
# END SITE CONFIGURATION

INSTALLED_APPS += ("gunicorn", )

# STORAGE CONFIGURATION
# ------------------------------------------------------------------------------
# Uploaded Media Files
# ------------------------
# See: http://django-storages.readthedocs.org/en/latest/index.html
INSTALLED_APPS += (
    'storages',
)
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
#
# AWS_ACCESS_KEY_ID = env('DJANGO_AWS_ACCESS_KEY_ID')
# AWS_SECRET_ACCESS_KEY = env('DJANGO_AWS_SECRET_ACCESS_KEY')
# AWS_STORAGE_BUCKET_NAME = env('DJANGO_AWS_STORAGE_BUCKET_NAME')
# AWS_AUTO_CREATE_BUCKET = True
# AWS_QUERYSTRING_AUTH = False
# AWS_S3_CALLING_FORMAT = OrdinaryCallingFormat()
#
# # AWS cache settings, don't change unless you know what you're doing:
# AWS_EXPIRY = 60 * 60 * 24 * 7
#
# # TODO See: https://github.com/jschneier/django-storages/issues/47
# # Revert the following and use str after the above-mentioned bug is fixed in
# # either django-storage-redux or boto
# AWS_HEADERS = {
#     'Cache-Control': six.b('max-age=%d, s-maxage=%d, must-revalidate' % (
#         AWS_EXPIRY, AWS_EXPIRY))
# }
#
# # URL that handles the media served from MEDIA_ROOT, used for managing
# # stored files.
# MEDIA_URL = 'https://s3.amazonaws.com/%s/' % AWS_STORAGE_BUCKET_NAME
MEDIA_ROOT = '/var/www/mobovidata/media'

# Static Assets
# ------------------------

# STATICFILES_STORAGE = DEFAULT_FILE_STORAGE
# STATIC_URL = MEDIA_URL
#
# # See: https://github.com/antonagestam/collectfast
# # For Django 1.7+, 'collectfast' should come before
# # 'django.contrib.staticfiles'
# AWS_PRELOAD_METADATA = True
# INSTALLED_APPS = ('collectfast', ) + INSTALLED_APPS

# EMAIL
# ------------------------------------------------------------------------------

# DEFAULT_FROM_EMAIL = env('DJANGO_DEFAULT_FROM_EMAIL',
#                          default='mobovidata <noreply@mobovidata.com>')
# EMAIL_BACKEND = 'django_mailgun.MailgunBackend'
# MAILGUN_ACCESS_KEY = env('DJANGO_MAILGUN_API_KEY')
# MAILGUN_SERVER_NAME = env('DJANGO_MAILGUN_SERVER_NAME')
# EMAIL_SUBJECT_PREFIX = env("DJANGO_EMAIL_SUBJECT_PREFIX", default='[mobovidata_www] ')
# SERVER_EMAIL = env('DJANGO_SERVER_EMAIL', default=DEFAULT_FROM_EMAIL)

# Mail settings (from local.py)
# ------------------------------------------------------------------------------
# EMAIL_HOST = 'localhost'
# EMAIL_PORT = 25
# EMAIL_BACKEND = env('DJANGO_EMAIL_BACKEND',
#                     default='django.core.mail.backends.console.EmailBackend')
# DEFAULT_FROM_EMAIL = 'Pinplub <pangryn@staging.mobovidata.com>'

EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_ACCESS_KEY_ID = os.environ.get('SES_KEY')
AWS_SECRET_ACCESS_KEY = os.environ.get('SES_SECRET')
AWS_SES_REGION_NAME = 'us-west-2'
AWS_SES_REGION_ENDPOINT = 'email.us-west-2.amazonaws.com'
SERVER_EMAIL = 'kenny@mobovida.com'
DEFAULT_FROM_EMAIL = 'kenny@mobovida.com'
EMAIL_SUBJECT_PREFIX = '[MVD] '


# TEMPLATE CONFIGURATION
# ------------------------------------------------------------------------------
# See:
# https://docs.djangoproject.com/en/dev/ref/templates/api/#django.template.loaders.cached.Loader
# TEMPLATES[0]['OPTIONS']['loaders'] = [
#     ('django.template.loaders.cached.Loader', [
#         'django.template.loaders.filesystem.Loader', 'django.template.loaders.app_directories.Loader', ]),
# ]

# DATABASE CONFIGURATION
# ------------------------------------------------------------------------------
# Raises ImproperlyConfigured exception if DATABASE_URL not in os.environ
# DATABASES['default'] = env.db("DATABASE_URL")


# CACHING
# ------------------------------------------------------------------------------
# Heroku URL does not pass the DB number, so we parse it in
# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": "{0}/{1}".format(env('REDIS_URL', default="redis://127.0.0.1:6379"), 0),
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#             "IGNORE_EXCEPTIONS": True,  # mimics memcache behavior.
#                                         # http://niwinz.github.io/django-redis/latest/#_memcached_exceptions_behavior
#         }
#     }
# }


# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#         'LOCATION': ''
#     }
# }
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


# LOGGING CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#logging
# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'filters': {
#         'require_debug_false': {
#             '()': 'django.utils.log.RequireDebugFalse'
#         }
#     },
#     'formatters': {
#         'verbose': {
#             'format': '%(levelname)s %(asctime)s %(module)s '
#                       '%(process)d %(thread)d %(message)s'
#         },
#     },
#     'handlers': {
#         'mail_admins': {
#             'level': 'ERROR',
#             'filters': ['require_debug_false'],
#             'class': 'django.utils.log.AdminEmailHandler'
#         },
#         'console': {
#             'level': 'DEBUG',
#             'class': 'logging.StreamHandler',
#             'formatter': 'verbose',
#         },
#     },
#     'loggers': {
#         'django.request': {
#             'handlers': ['mail_admins'],
#             'level': 'ERROR',
#             'propagate': True
#         },
#         'django.security.DisallowedHost': {
#             'level': 'ERROR',
#             'handlers': ['console', 'mail_admins'],
#             'propagate': True
#         }
#     }
# }

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    # Configure root logger to only accept ERROR level messages. Discard anything less severe than ERROR.
    # Handler does something with the message. In this case, root passes messages to the sentry handler
    'root': {
        'level': 'WARNING',
        'handlers': ['sentry', 'sentry_warning'],
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s '
                      '%(process)d %(thread)d %(message)s'
        },
        'console-brief': {
            u'format':           u'%(message)s',
            u'()':               u'djenga.loggers.BriefColorFormatter',
        },
    },
    'handlers': {
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.handlers.SentryHandler',
            'formatter': 'verbose'
        },
        'sentry_warning': {
            'level': 'WARNING',
            'class': 'raven.contrib.django.handlers.SentryHandler',
            'formatter': 'verbose'
        },
        'sentry_info': {
            'level': 'INFO',
            'class': 'raven.contrib.django.handlers.SentryHandler',
            'formatter': 'verbose'
        },
        'console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'console_debug': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'console-brief',
        },
    },
    'loggers': {
        'sentry.errors': {
            'level': 'WARNING',
            'handlers': ['console'],
            'propagate': False,
        },
        'management_command': {
            'level': 'DEBUG',
            'handlers': ['console_debug'],
            'propagate': True,
        },
    },
}

# Custom Admin URL, use {% url 'admin:index' %}
# ADMIN_URL = env('DJANGO_ADMIN_URL')

# Production celery tasks
if os.environ.get('ENV_TYPE') == 'production':
    CELERYBEAT_SCHEDULE['get-inventory'] = {
        'task': 'mobovidata_dj.salesreport.tasks.get_inventory',
        'schedule': crontab(hour=5, minute=1),
    }
    CELERYBEAT_SCHEDULE['get-inventory-cogs'] = {
        'task': 'mobovidata_dj.salesreport.tasks.get_inventory_cogs',
        'schedule': crontab(hour=5, minute=5),
    }
    CELERYBEAT_SCHEDULE['get-inventory-special-price'] = {
        'task': 'mobovidata_dj.salesreport.tasks.get_inventory_special_price',
        'schedule': crontab(hour=5, minute=10),
    }
    CELERYBEAT_SCHEDULE['get-inventory-retail-price'] = {
        'task': 'mobovidata_dj.salesreport.tasks.get_inventory_retail_price',
        'schedule': crontab(hour=5, minute=15),
    }
    CELERYBEAT_SCHEDULE['post-s3-data'] = {
        'task': 'mobovidata_dj.reports.tasks.execute_recurring_s3',
        'schedule': crontab(hour=3, minute=30),
    }
    CELERYBEAT_SCHEDULE['load-redshift-data'] = {
        'task': 'mobovidata_dj.reports.tasks.execute_redshift_tables',
        'schedule': crontab(hour=3, minute=0),
    }
    CELERYBEAT_SCHEDULE['sync-contact-list'] = {
        'task': 'mobovidata_dj.emails.tasks.sync_contact_list',
        'schedule': crontab(hour=1, minute=0),
    }
    CELERYBEAT_SCHEDULE['update-last-thirty-days-stats'] = {
        'task': 'mobovidata_dj.facebook.tasks.update_last_thirty_days_stats',
        'schedule': crontab(hour=1, minute=30),
    }
    CELERYBEAT_SCHEDULE['drop-and-load-opt-out-emails-table'] = {
        'task': 'mobovidata_dj.responsys.tasks.drop_and_load_opt_out_emails_table',
        'schedule': crontab(hour=1, minute=15),
    }
    # CELERYBEAT_SCHEDULE['update_previous_day_stats'] = {
    #     'task': 'mobovidata_dj.facebook.tasks.update_last_thirty_days_stats',
    #     'schedule': timedelta(days=3),
    # }

# Your production stuff: Below this line define 3rd party library settings
JOB_WORKERS = 4
S3_SQL_BACKUP_BUCKET = os.environ.get('S3_SQL_BACKUP_BUCKET')
S3_SENDDATA_BACKUP_BUCKET = os.environ.get('S3_SENDDATA_BACKUP_BUCKET')


RESPONSYS_LIST_FOLDER = '!MageData'
RESPONSYS_CONTACT_LIST = 'CONTACT_LIST'

PRODUCT_FEED_DIR_NAME = 'feeds'
PRODUCT_FEED_DIR = os.path.join(MEDIA_ROOT, PRODUCT_FEED_DIR_NAME)
