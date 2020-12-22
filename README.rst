Getting started with local development
==============================

1. Check out the code:

        git clone git@bitbucket.org:wirelessemporium/mobovidata.git mobovidata

        cd mobovidata/

2. Set up a virtual environment:

        virtualenv .env

This creates a virtual environment in the .env dir in your project's directory, our default setup for mobovidata.

3. Activate the virtual env:

        source .env/bin/activate

4. Install MySQL/MariaDB, then run:

        mysql -h localhost -e "create database mobovidata;"

This will be used for Django's own tables and any models we add outside of Magento.
(Adjust your connection settings for your local mysql as needed.)

5. Install requirements:

        pip install -r requirements/development.txt

6. Create a local MySQL database; this will be used for Django's own tables and any models we add outside of Magento:

        from .common import *

        DATABASES['default'].update({
          ... # Your settings from step 5 above
        })

7. Create your local settings override, `config/settings/local.py` & create a user named 'django' in MySQL:

    		from .common import *

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
            'NAME': 'dev.mobilegiant.ca',
            'PASSWORD': 'YOUR PASSWORD HERE',
            'PORT': '3306',
            'USER': 'django'
        }
        DATABASES['crate'].update({
            "SERVERS": ["138.68.10.226:4201",],
            "NAME": "crate",
        })

8. Check out the `dev` branch:

        git checkout -t origin/dev

All future work should be based off and pull requested to the `dev` branch.


Settings Setup
--------------
Additional settings will be added to your local.py as needed.

Crate Setup
-----------
Crate is an ElasticSearch-based frontend that we use to store our massive email logs.
When provisioning a new server you need to configure fabric settings and then run

        fab migrate_crate:target=TARGET,branch=BRANCH

 For local setup, checkout the README in mobovidata_dj/emails/README.md

Loading magento locally
-----------------------
Normally we would like to test in our local before pushing code into staging, so we need to load data in our local db regularly.
For local setup, checkout the README in modjento/README.md
=======

Deployment process
------------------
Run:

        fab deploy:target=TARGET,branch=BRANCH
