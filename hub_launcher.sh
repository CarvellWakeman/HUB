#!/bin/sh -e
# launcher.sh
# navigate to home directory, then to this directory, then execute python script, then back home

cd /
cd home/cooper/hub
sudo python3 hub_server.py
cd /