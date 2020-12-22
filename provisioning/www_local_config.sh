#!/usr/bin/env bash
# To be run after www_user_config.sh, when current user is UNAME

UGROUP=www_app_group
UNAME=www_user
UHOME=/www_app_group/mobovidata/

cd $UHOME
virtualenv .env

#source bin/activate
