#!/bin/sh

# PATCH MINION - CENTOS MACHINE (TESTED)

echo "Creating patch-minion folder"
mkdir -p /opt/patch-minion/source
cd /opt/patch-minion/source
# INSTALLING PATCH-MINION DEPENDENCIES
# Installing virtual env
echo "Installing virtualenv"
yum -y install python-virtualenv
# Creating virtual environment of python
echo "Creating virtualenv -- env"
virtualenv --distribute  /opt/patch-minion/env
# Activating environment
echo "Created"
echo "Activating env"
source /opt/patch-minion/env/bin/activate
cd /opt/patch-minion/source
echo "Installing pip dependencies"
pip install -r requires.txt
deactivate
echo "Finished - dependencies"

# Setting up service 
echo "Setting up service for patch-minon"
cp /opt/patch-minion/source/patch-minion.service /etc/systemd/system/patch-minion.service
systemctl enable patch-minion.service
systemctl start patch-minion.service
systemctl status patch-minion.service

echo ""
echo " - COMPLETED - "
echo ""
echo " To verify - open web browser with http://localhost:8082"