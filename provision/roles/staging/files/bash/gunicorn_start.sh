#!/bin/bash

NAME="mobovidata"                                  # Name of the application
DJANGODIR=/usr/local/lib/mobovidata/
SOCKFILE=/usr/local/lib/mobovidata/run/gunicorn.sock  # we will communicate using this unix socket
config.wsgi:application
USER=www-data                                        # the user to run as
GROUP=www-data                                     # the group to run as
NUM_WORKERS=3                                     # how many worker processes should Gunicorn spawn
DJANGO_SETTINGS_MODULE=config.settings.production           # which settings file should Django use
DJANGO_WSGI_MODULE=config.wsgi                     # WSGI module name


echo "Starting $NAME as `whoami`"

# Activate the virtual environment
cd $DJANGODIR
source env/bin/activate
DJANGO_SECRET_KEY=%(DJANGO_SECRET_KEY)s,
MAGENTO_PASSWORD=%(MAGENTO_PASSWORD)s,
FACEBOOK_APP_ID=%(FACEBOOK_APP_ID)s,
FACEBOOK_APP_SECRET=%(FACEBOOK_APP_SECRET)s,
FACEBOOK_USER_TOKEN=%(FACEBOOK_USER_TOKEN)s,
FACEBOOK_ACCOUNT_ID=%(FACEBOOK_ACCOUNT_ID)s,
FACEBOOK_PAGE_ID=%(FACEBOOK_PAGE_ID)s
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH
export DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY
export DJANGO_CUSTOM_SETTINGS_DB_NAME=$DJANGO_CUSTOM_SETTINGS_DB_NAME

# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR

# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
exec .env/bin/gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $NUM_WORKERS \
  --user=$USER --group=$GROUP \
  --bind=unix:$SOCKFILE \
  --log-level=debug \
  --log-file=- \
  --access-logfile=/var/log/mobovidata/access.log \
  --error-logfile=/var/log/mobovidata/error.log
