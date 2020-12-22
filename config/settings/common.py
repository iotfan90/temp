# -*- coding: utf-8 -*-
"""
Django settings for mobovidata_www project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""
from celery.schedules import crontab
from datetime import timedelta

import environ
import os


ROOT_DIR = environ.Path(__file__) - 3  # (/a/b/myfile.py - 3 = /)
APPS_DIR = ROOT_DIR.path('mobovidata_dj')

env = environ.Env()

# APP CONFIGURATION
# ------------------------------------------------------------------------------
DJANGO_APPS = (
    # Default Django apps:
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Useful template tags:
    'django.contrib.humanize',

    # Admin
    'django.contrib.admin',
)
THIRD_PARTY_APPS = (
    'crispy_forms',  # Form layouts
    'allauth',  # registration
    'allauth.account',  # registration
    'allauth.socialaccount',  # registration
    'corsheaders',  # cross-site ajax
    'djcelery',  # distributed tasks
    # 'rest_framework',
    'adminsortable',  # For making filters sortable/orderable via the admin
    'polymorphic',  # Polymorhpic relationships (for handling Filters & Senders)
    'rest_framework',
    'django_assets',
    'raven.contrib.django.raven_compat',
    'django_extensions',
    'taggit',
    'rangefilter',
    'debug_toolbar'
    # 'registration', # authorization-approval
    # 'registration.supplements.default',
)

# Apps specific for this project go here.
LOCAL_APPS = (
    'mobovidata_dj.users',  # custom users app
    'mobovidata_dj.analytics',  # analytics management
    'mobovidata_dj.responsys',  # Responsys email management
    'mobovidata_dj.core',  # Shared models
    'mobovidata_dj.lifecycle',  # Customer lifecycle messaging
    'mobovidata_dj.salesreport',  # Sales Report
    'mobovidata_dj.helpscout',  # HelpScout
    'mobovidata',
    'modjento',
    'mobovidata_dj.feeds',
    'kpi',
    'mobovidata_dj.ltv',
    'mobovidata_dj.shopify',
    'mobovidata_dj.emails',
    'mobovidata_dj.bigdata',
    'mobovidata_dj.omniture',
    'mobovidata_dj.facebook',
    'mobovidata_dj.reports',
    'mobovidata_dj.imageretrieval',
    'supplier_inventory',
    'mobovidata_dj.webhooks'
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# MIDDLEWARE CONFIGURATION
# ------------------------------------------------------------------------------
MIDDLEWARE_CLASSES = (
    # Make sure djangosecure.middleware.SecurityMiddleware is listed first
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware'
    # 'mobovidata_dj.users.middleware.RequireLoginMiddleware', # Require logins by default
)


# MIGRATIONS CONFIGURATION
# ------------------------------------------------------------------------------
MIGRATION_MODULES = {
    'sites': 'mobovidata_dj.contrib.sites.migrations'
}

# DEBUG
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env.bool("DJANGO_DEBUG", False)

# FIXTURE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-FIXTURE_DIRS
FIXTURE_DIRS = (
    str(APPS_DIR.path('fixtures')),
)

# EMAIL CONFIGURATION
# ------------------------------------------------------------------------------
EMAIL_BACKEND = env('DJANGO_EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')

# MANAGER CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = (
    ("""Federico Comesana""", 'federico@mobovida.com'),
    ("""Kenny Smithnanic""", 'kenny@mobovida.com'),
    ("""Ali Kashani""", 'ali@mobovida.com'),
    ("""Yuki""", 'yuki@mobovida.com'),
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS

# DATABASE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mobovidata_www',
        'USER': 'django',
        'PASSWORD': 'ripcurl',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            "init_command": "SET storage_engine=InnoDB; set time_zone='UTC';",
        },
    },
    'magento': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('MAGENTO_DB', 'dev.mobilegiant.ca',),
        'USER': os.environ.get('MAGENTO_USER'),
        'HOST': os.environ.get('MAGENTO_IP'),
        'PASSWORD': os.environ.get('MAGENTO_PASSWORD'),
        'PORT': os.environ.get('MAGENTO_PORT'),
        'OPTIONS': {
            "init_command": "SET storage_engine=InnoDB; set time_zone='UTC';",
        },
    },
}

DATABASES['default']['ATOMIC_REQUESTS'] = True

DATABASE_ROUTERS = (
    'mobovidata_dj.routers.MagentoRouter',
)


# GENERAL CONFIGURATION
# ------------------------------------------------------------------------------
# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Los_Angeles'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = 'en-us'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True

# TEMPLATE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [
    {
        # See: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
        'DIRS': [
            str(APPS_DIR.path('templates')),
        ],
        'OPTIONS': {
            # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-debug
            'debug': DEBUG,
            # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-loaders
            # https://docs.djangoproject.com/en/dev/ref/templates/api/#loader-types
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
            # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                # Your stuff: custom template context processors go here
                'mobovidata.context_processors.google_analytics.google_analytics',
            ],
        },
    },
]

# See: http://django-crispy-forms.readthedocs.org/en/latest/install.html#template-packs
CRISPY_TEMPLATE_PACK = 'bootstrap3'

# STATIC FILE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = str(ROOT_DIR('static'))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = '/static/'

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = (
    str(APPS_DIR.path('static')),
)

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django_assets.finders.AssetsFinder',
)

# MEDIA CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = str(ROOT_DIR('media'))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = '/media/'

# URL Configuration
# ------------------------------------------------------------------------------
ROOT_URLCONF = 'config.urls'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = 'config.wsgi.application'

# AUTHENTICATION CONFIGURATION
# ------------------------------------------------------------------------------
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

# Some really nice defaults
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_ADAPTER = 'mobovidata_dj.users.adapter.AccountAdapter'
SOCIALACCOUNT_ADAPTER = 'mobovidata_dj.users.adapter.SocialAccountAdapter'
ACCOUNT_ALLOW_REGISTRATION = False


# Custom user app defaults
# Select the correct user model
AUTH_USER_MODEL = 'users.User'
LOGIN_REDIRECT_URL = 'users:redirect'
LOGIN_URL = 'account_login'

# SLUGLIFIER
AUTOSLUG_SLUGIFY_FUNCTION = 'slugify.slugify'

# LOGIN_REQUIRED_URLS = (
#     r'/responsys/$',
# )


# CELERY
INSTALLED_APPS += ('mobovidata_dj.taskapp.celery_app.CeleryConfig',)
# if you are not using the django database broker (e.g. rabbitmq, redis, memcached), you can remove the next line.
INSTALLED_APPS += ('kombu.transport.django',)
# CELERY STUFF
BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Los_Angeles'
CELERYBEAT_SCHEDULE = {
    # 'run-campaigns': {
    #     'task': 'mobovidata_dj.lifecycle.tasks.run_campaigns',
    #     'schedule': timedelta(minutes=5)
    # },
    # 'update-responsys-auth': {
    #     'task': 'mobovidata_dj.responsys.tasks.get_update_responsys_token',
    #     'schedule': timedelta(minutes=30)
    # },
    # 'reset_cart_abandon_lifecycle_stage': {
    #     'task': 'mobovidata_dj.lifecycle.tasks.reset_cart_abandon_lifecycle_stage',
    #     'schedule': timedelta(days=2)
    # },
    'get-sales-report': {
        'task': 'mobovidata_dj.salesreport.tasks.get_sales_report',
        # 'schedule': timedelta(days=1)
        'schedule': crontab(hour=0, minute=1)
    },
    'make_feeds': {
        'task': 'mobovidata_dj.feeds.tasks.make_feeds',
        'schedule': crontab(hour=10, minute=20)
    },
    'update-helpscout-responsys': {
        'task': 'mobovidata_dj.helpscout.tasks.update_helpscout',
        'schedule': timedelta(days=1)
    },
    'exclude-canceled-order-email': {
        'task': 'mobovidata_dj.lifecycle.tasks.exclude_canceled_order_email',
        'schedule': timedelta(days=1)
    },
    'process-new-orders': {
        'task': 'mobovidata_dj.ltv.tasks.process_new_orders',
        'schedule': crontab(hour=1, minute=0)
    },
    'track_email_sign_ups': {
        'task': 'mobovidata_dj.analytics.tasks.email_sign_up_track',
        'schedule': crontab(hour=8, minute=0)
    },
    # 'update_shopify_inventory': {
    #     'task': 'mobovidata_dj.shopify.tasks.update_shopify_inventory',
    #     'schedule': timedelta(hours=1)
    # },
    # 'run_order_confirmation': {
    #     'task': 'mobovidata_dj.lifecycle.tasks.run_order_confirmation',
    #     'schedule': timedelta(minutes=5)
    # },
    # 'update_subscriptions_status': {
    #     'task': 'mobovidata_dj.responsys.tasks.update_subscriptions_status',
    #     'schedule': timedelta(days=1)
    # },
    'start_due_jobs': {
        'task': 'mobovidata_dj.taskapp.celery_app.start_due_jobs',
        'schedule': timedelta(seconds=15)
    },
    # 'check_responsys_api_cache': {
    #     'task': 'mobovidata_dj.responsys.tasks.check_cache',
    #     'schedule': timedelta(days=1)
    # },
    'repeat_customers_cache': {
        'task': 'mobovidata_dj.ltv.tasks.repeat_customers_cache',
        'schedule': crontab(hour=1, minute=30)
    },
    'update_supplier_inventory': {
        'task': 'supplier_inventory.tasks.import_supplier_inventory',
        'schedule': crontab(hour=0, minute=45)
    },
    # 'run_shipping_confirmation': {
    #     'task': 'mobovidata_dj.lifecycle.tasks.run_shipping_confirmation',
    #     'schedule': timedelta(minutes=10)
    # },
    # 'send_nps_emails': {
    #     'task': 'mobovidata_dj.lifecycle.tasks.run_nps_emails',
    #     'schedule': timedelta(hours=1)
    # },
    # 'run_search_abandon': {
    #     'task': 'mobovidata_dj.lifecycle.tasks.run_search_abandon',
    #     'schedule': timedelta(minutes=5)
    # },
    'update_customer_devices': {
        'task': 'mobovidata_dj.analytics.tasks.update_customer_devices',
        'schedule': timedelta(minutes=60)
    },
    # 'update_riid_email_table': {
    #     'task': mobovidata_dj.analytics.tasks.update_riid_email_table',
    #     'schedule': timedelta(hours=24)
    # },
    # 'upload_nps_responsys': {
    #     'task': 'mobovidata_dj.responsys.tasks.upload_nps_responsys',
    #     'schedule': timedelta(hours=24)
    # },
    # 'upload_shipping_status_responsys': {
    #     'task': 'mobovidata_dj.lifecycle.tasks.check_upload_shipping_status_responsys',
    #     'schedule': timedelta(hours=24)
    # },
}

# JOB_WORKERS are celery workers dedicated to doing long-running ETL jobs
# We tune this to be smaller than the total number of celery workers,
# so that we never fully clog the queue with 10-threads x 20hours of work
# Suggested production value: 50-75% of the # of available workers
JOB_WORKERS = 4

# Location of root django.contrib.admin URL, use {% url 'admin:index' %}
ADMIN_URL = r'^admin/'

# Your common stuff: Below this line define 3rd party library settings

# Define allowed domains for cross-site ajax calls
CORS_ORIGIN_WHITELIST = ('cellularoutfitter.com',
                         'www.cellularoutfitter.com',
                         'www.wirelessemporium.com',
                         'www.missminx.com',
                         'localhost:8000',
                         'staging.cellularoutfitter.com',
                         'https://fiddle.jshell.net/',
                         'https://mobovida.com',
                         'https://t.mobovidata.com',
                         't.mobovidata.com', )

CORS_ORIGIN_REGEX_WHITELIST = ('^(https?://)?(.+\.)?myshopify\.com',
                               '^(https?://)?(.+\.)?mobovida\.com',
                               '^(https?://)t\.mobovidata\.com')

RESPONSYS_AUTH = {'auth_url': 'https://login5.responsys.net/rest/api/v1/auth/token',
                  'password': os.environ.get('RESPONSYS_PW'),
                  'user_name': 'rest_user'}

RESPONSYS_ENDPOINTS = {'campaign': '/rest/api/v1/campaigns/',
                       'event': '/rest/api/v1/events/'}

MAGENTO_URL_PREFIXES = {'img': 'http://www.cellularoutfitter.com/media/catalog/product',
                        'pdp': 'http://www.cellularoutfitter.com/',
                        'search': 'https://www.cellularoutfitter.com/search/result?q='}

SHOPIFY_URL_PREFIXES = {'pdp': 'https://shop.wirelessemporium.com/'}


FACEBOOK_API = {
    'app_id': os.environ.get('FACEBOOK_APP_ID'),
    'app_secret': os.environ.get('FACEBOOK_APP_SECRET'),
    'user_token': os.environ.get('FACEBOOK_USER_TOKEN'),
    'account_id': os.environ.get('FACEBOOK_ACCOUNT_ID'),
    'page_id': os.environ.get('FACEBOOK_PAGE_ID'),
    'instagram_actor_id': os.environ.get('INSTAGRAM_ACCOUNT_ID'),
    'version': 'v2.9',
}

ASSETS_DEBUG = False
ASSETS_AUTO_BUILD = True
ASSETS_URL_EXPIRE = True

SENTRY_TESTING = True  # Set to True to test sentry even when DEBUG=True
SENTRY_DSN = os.environ.get('SENTRY_DSN')

SHELL_PLUS = 'ipython'

GOOGLE_ANALYTICS_PROPERTY_ID = os.environ.get('GOOGLE_ANALYTICS_PROPERTY_ID')

HELPSCOUT_MAILBOXES = ['4501', '4498', '4499', '4502', '25252', '20311', '29511', '29616', '29512', '54115']

STRANDS_ENDPOINT = 'http://bizsolutions.strands.com/api2/recs/item/get.sbs'
STRANDS_APID = os.environ.get('STRANDS_APID')
MANDRILL_API_KEY = os.environ.get('MANDRILL_API_KEY')
MANDIRLL_API_ROOT = 'https://mandrillapp.com/api/1.0/'
MANDRILL_FROM_EMAIL = 'support@coremail.cellularoutfitter.com'
MANDRILL_FROM_NAME = 'Cellular Outfitter'
MANDRILL_REPLY_TO_EMAIL = 'support@email.cellularoutfitter.com'

PRODUCT_FEED_DIR_NAME = 'feeds'
PRODUCT_FEED_DIR = os.path.join(MEDIA_ROOT, PRODUCT_FEED_DIR_NAME)

RESPONSYS_FEED = {
    'feed_name': os.path.join(PRODUCT_FEED_DIR, 'resp_co_com.csv'),
    'tracking_string': '',
    'destination': '/home/cli/wirelessemp_scp/upload/',
}

RESPONSYS_FTP = {
    'pkey': './.ssh/responsys_key.key',
    'url': 'files.dc2.responsys.net',
    'user': 'wirelessemp_scp',
}

DY_FTP = {
    'host':  'ftp1.use.dynamicyield.com',
    'user': 'mobovida',
    'pkey': './.ssh/mobovidata_app.key',
}

DY_FEED_PATH = 'https://www.cellularoutfitter.com/media/feed/datafeed_dynamicyield_co.zip'

RESPONSYS_EMAIL_PATH = {
    'dir': '/home/cli/wirelessemp_scp/archive/',
    'in': '54084_OPT_IN_',
    'out': '54084_OPT_OUT_',
    'local': './data/responsys/'
}

RESPONSYS_SEND_DATA_PATH = {
    'dir': '/home/cli/wirelessemp_scp/download/CED_Data',
    'tgt': './data/send_data'
}

RESPONSYS_COLUMN_MAP = {
    "image_link": "IMAGE_LINK",
    "c:retail_price": "RETAIL_PRICE",
    "c:cell_phone_model": "PHONE_MODEL",
    "quantity": "QUANTITY",
    "color": "COLOR",
    "title": "TITLE",
    "adwords_labels": "PRODUCT_CATEGORY",
    "price": "PRICE",
    "brand": "BRAND",
    "id": "PRODUCT_ID",
    "mpn": "SKU",
}

RESPONSYS_CONTACT_EVENT_DATA_MAP = {
    'unsubscribe': '7',
    'subscribe': '21',
}

FACEBOOK_FEED = {
    'tracking_string': ('?DZID=Facebook_OCPM_feed_'
                        '%s_&utm_source=facebook&u'
                        'tm_medium=ocpm&utm_campaign=facebook_feed'),
    'feed_name': os.path.join(PRODUCT_FEED_DIR, 'facebook_feed.csv'),
    'separate_feed_name': os.path.join(PRODUCT_FEED_DIR, 'separate_facebook_feed.csv'),
    'facebook_bluetooth_feed': os.path.join(PRODUCT_FEED_DIR, 'facebook_bluetooth_feed.csv'),
}

TESTEFFECTS_FTP = {
    'pass': os.environ.get('TESTEFFECTS_FTP_PASS'),
    'url': '2b5.939.myftpupload.com',
    'user': 'kennysmith1'
}

FACEBOOK_COLUMN_MAP = {
    'title': 'title',
    'description': 'description',
    'image_link': 'image_link',
    'condition': 'condition',
    'c:retail_price': 'price',
    'price': 'sale_price',
    'id': 'id',
    'mpn': 'mpn',
    'quantity': 'inventory',
    'c:cell_phone_model': 'brand',
    'Custom Label 1': 'product_type',
    'adwords_grouping': 'custom_label_0',
    'color': 'color',
    'google_product_category': 'google_product_category',
    'link': 'link',
}

GOOGLEBASE_FEED_CO = 'http://www.cellularoutfitter.com/media/feed/datafeed_googlebase_co.zip'

BLOOMREACH_FEED_CO = 'http://www.cellularoutfitter.com/media/feed/datafeed_bloomreach_co.zip'

HELPSCOUT_API = {
    'endpoint': os.environ.get('HELPSCOUT_API_ENDPOINT'),
    'api_key': os.environ.get('HELPSCOUT_API_KEY'),
}

MAILCHIMP_API_KEY = os.environ.get('MAILCHIMP_API_KEY')
MAILCHIMP_ENDPOINT = 'https://us13.api.mailchimp.com/3.0'


GA_SCOPE = 'https://www.googleapis.com/auth/analytics.readonly'
GA_ACCOUNT_ID = '1097464'
GA_PROFILE_ID = 'ga:96468820'
GA_KEYFILE = '/etc/ssl/private/mad-gentoo.credentials.json'

SHOPIFY = {
    'API_KEY': os.environ.get('SHOPIFY_API_KEY'),
    'PASSWORD': os.environ.get('SHOPIFY_API_PASSWORD'),
    'WIRELESS_EMPORIUM_URL': 'wireless-emporium-store.myshopify.com',
    'MOBOVIDA_URL': os.environ.get('mobovida.myshopify.com')
}

SLICKTEXT = {
    'endpoint': os.environ.get('SLICKTEXT_ENDPOINT'),
    'user': os.environ.get('SLICKTEXT_USER'),
    'pw': os.environ.get('SLICKTEXT_PW')
}

EMAIL_DATA_PATH = './send_data/'
S3_BACKUP_KEY = os.environ.get('S3_BACKUP_KEY')
S3_BACKUP_SECRET = os.environ.get('S3_BACKUP_SECRET')
S3_SQL_BACKUP_BUCKET = 'mobovidata-sql-backup'
S3_SENDDATA_BACKUP_BUCKET = 'mobovidata-senddata-backup'
S3_REPORT_BUCKET = 'mobovidata-reports'
ROOT_DOMAIN = os.environ.get('DOMAIN', 'http://localhost:8000')
REDSHIFT_DB = os.environ.get('REDSHIFT_DB')
REDSHIFT_USER = os.environ.get('REDSHIFT_USER')
REDSHIFT_PASSWORD = os.environ.get('REDSHIFT_PASSWORD')
REDSHIFT_ENDPOINT = os.environ.get('REDSHIFT_ENDPOINT')

OMNITURE_CREDENTIALS = {
    'username': os.environ.get('OMNITURE_USER'),
    'secret': os.environ.get('OMNITURE_SECRET'),
    'report_suite_ids': [os.environ.get('OMNITURE_REPORT_SUITES')]
}

SUPPLIER_INFO = {
    'HR': {
        'id': 11,
        'feed_url': 'http://www.hrwireless.com/export-full-quantity-csv.asp',
    }
}


FACEBOOK_SEPERATE_IDS = [
    '55617',
    '55615',
    '55616',
    '55613',
    '55619',
    '55614',
    '55618',
    '53381',
    '53379',
    '53382',
    '53388',
    '53387',
    '52291',
    '53380',
    '53386',
    '53383',
    '53384',
    '53553',
    '53552',
    '53551',
    '53550',
    '53549',
    '53548',
]


PO_DEFAULTS = {
    'default_avg_weights': [0.24, 0.19, 0.1, 0.2, 0.31, 0.1],
    'lead_time': 7.0,
    'days_between': 7.0,
    'service_level': 0.8
}

RESPONSYS_UNBOUNCE_EVENT = 'unbounce1'
if DEBUG:
    RESPONSYS_LIST_FOLDER = '!StagingData'
    RESPONSYS_CONTACT_LIST = 'CONTACT_LIST_STAGING'
else:
    RESPONSYS_LIST_FOLDER = '!MageData'
    RESPONSYS_CONTACT_LIST = 'CONTACT_LIST'


TAGGIT_CASE_INSENSITIVE = True

DOMAIN_URL = 'https://t.mobovidata.com'

# FTP Stone Edge
FTP_STONE_EDGE_DOMAIN = os.environ.get('FTP_STONE_EDGE_DOMAIN')
FTP_STONE_EDGE_PORT = os.environ.get('FTP_STONE_EDGE_PORT')
FTP_STONE_EDGE_USER = os.environ.get('FTP_STONE_EDGE_USER')
FTP_STONE_EDGE_PASSWORD = os.environ.get('FTP_STONE_EDGE_PASSWORD')
FTP_STONE_EDGE_FOLDER_PATH = os.environ.get('FTP_STONE_EDGE_FOLDER_PATH')

DS_HR_URL = 'http://www.hrwireless.com/export-full-quantity-csv.asp'
ALPHAVANTAGE_API_KEY = 'B3IFUJRGZE46YR1R'

SHOPIFY_CDN_FILES_URL = 'https://cdn.shopify.com/s/files/1/2012/3181/files/'

RETENTIONSCIENCE = {
    'host': 'sftp1.retentionscience.com',
    'user': 'cellularoutfitter',
    'password': 'd9f4002636a225e9751e',
}
