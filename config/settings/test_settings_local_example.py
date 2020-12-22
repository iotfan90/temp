"""
This is a Django local test settings example for mobovidata project.

You must create your own test_settings_local.py file using this template and
replacing the fields with your own data.

Additional settings will be added to your test_settings_local.py as needed.
"""

import os

DATABASES = {}

# DATABASE CONFIGURATION
# ------------------------------------------------------------------------------
if not os.environ.get('ENV_TYPE'):
    DATABASES['magento'] = {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': '127.0.0.1',
        'NAME': 'YOUR DATABASE NAME',
        'PASSWORD': 'YOUR PASSWORD',
        'PORT': '3306',
        'USER': 'YOUR USER',
        'TEST': {
            'NAME': 'YOUR DATABASE NAME',
        }
    }
