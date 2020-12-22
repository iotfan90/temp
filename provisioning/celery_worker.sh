#!/bin/bash

cd /www_app_group/mobovidata
source .env/bin/activate
celery worker -A mobovidata_dj.taskapp --loglevel=INFO
