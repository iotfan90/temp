"""
This is a Django local settings example for mobovidata project.

You must create your own local.py file using this template and
replacing the fields with your own data.

Additional settings will be added to your local.py as needed.
"""

from .common import *

DEBUG = True

# DATABASE CONFIGURATION
# ------------------------------------------------------------------------------
DATABASES['default'] = {
    'ENGINE': 'django.db.backends.mysql',
    'HOST': '127.0.0.1',
    'NAME': 'mobovidata',
    'PASSWORD': 'YOUR PASSWORD HERE',
    'PORT': '3306',
    'USER': 'django',
}
DATABASES['magento'] = {
    'ENGINE': 'django.db.backends.mysql',
    'HOST': '127.0.0.1',
    'NAME': 'mmg',
    'PASSWORD': 'YOUR PASSWORD HERE',
    'PORT': '3306',
    'USER': 'django'
}


# REDSHIFT DATABASE CONFIGURATION
# ------------------------------------------------------------------------------
REDSHIFT_DB = 'YOUR DB NAME HERE'
REDSHIFT_USER = 'YOUR USER HERE'
REDSHIFT_PASSWORD = 'YOUR PASSWORD HERE'
REDSHIFT_ENDPOINT = 'YOUR REDSHIFT ENDPOINT HERE'


# ORACLE RESPONSYS API CONFIGURATION
# ------------------------------------------------------------------------------
RESPONSYS_AUTH = {
    'auth_url': 'YOUR AUTH URL HERE',
    'password': 'YOUR PASSWORD HERE',
    'user_name': 'YOUR USERNAME HERE'
}


# FACEBOOK API CONFIGURATION
# ------------------------------------------------------------------------------
FACEBOOK_API = {
    'account_id': 'YOUR ACCOUNT ID HERE',
    'app_id': 'YOUR APP ID HERE',
    'app_secret': 'YOUR APP SECRET KEY HERE',
    'user_token': 'YOUR APP TOKEN HERE',
    'page_id': 'YOUR PAGE ID HERE',
    'instagram_actor_id': 'YOUR INSTAGRAM ACTOR ID HERE',
}
