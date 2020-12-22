#!/bin/bash
# Grant ownership to the appropriate users for the project dir

UGROUP=www_app_group
UNAME=www_user
UHOME=/www_app_group/mobovidata/

sudo chown -R $UNAME:users $UHOME
sudo chmod -R g+w $UHOME

sudo usermod -a -G users www_user


