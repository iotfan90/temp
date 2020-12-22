#!/bin/bash

cd /www_app_group/mobovidata
source .env/bin/activate
celerybeat -A mobovidata_dj.taskapp --loglevel=INFO
