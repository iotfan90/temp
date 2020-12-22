#!/usr/bin/env bash

# Activates virtualenv and sets some env vars
# execute as www_user

source .env/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production
export DJANGO_SECRET_KEY="8_mz5vt-d^db=t*vbgs6^%h)1qjud)8w_k2au1_^0&k#_t2x!7"

