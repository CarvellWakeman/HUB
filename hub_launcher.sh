#!/bin/sh -e
# /etc/rc0.d/hub_launcher.sh
# /etc/init.d/hub_launcher.sh
# navigate to home directory, then to this directory, then execute python script, then back home

cd /home/cooper/hub
sudo java -jar HubServer.jar 5000