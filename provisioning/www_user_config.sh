#!/bin/bash
# Create new user for web services and switch to that user

UGROUP=www_app_group
UNAME=www_user
UHOME=/www_app_group/mobovidata/


sudo groupadd --system $UGROUP
sudo useradd --system --gid $UGROUP --shell /bin/bash --home $UHOME $UNAME
#sudo mkdir -p $UHOME
#sudo chown $UNAME $UHOME
#
#sudo -u www_user -H bash -c "cd /www_app_group/"
