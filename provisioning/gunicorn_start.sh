#!/bin/bash

NAME="mobovidata_dj"                                  # Name of the application
DJANGODIR=/www_app_group/mobovidata/
SOCKFILE=/www_app_group/mobovidata/run/gunicorn.sock  # we will communicate using this unix socket
USER=www_user                                        # the user to run as
GROUP=www_app_group                                     # the group to run as
NUM_WORKERS=3                                     # how many worker processes should Gunicorn spawn
DJANGO_SETTINGS_MODULE=config.settings.production           # which settings file should Django use
DJANGO_WSGI_MODULE=config.wsgi                     # WSGI module name
DJANGO_SECRET_KEY='8_mz5vt-d^db=t*vbgs6^%h)1qjud)8w_k2au1_^0&k#_t2x!7'
DJANGO_CUSTOM_SETTINGS_DB_NAME="mobovidata_www"


echo "Starting $NAME as `whoami`"

# Activate the virtual environment
cd $DJANGODIR
source .env/bin/activate
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
  --log-file=-
