#!/bin/sh

cd /opt/
yum install -y wget unzip
wget https://github.com/pnkj-kmr/patch-minion/archive/master.zip -O patch-minion-master.zip
unzip patch-minion-master.zip
rm -rf patch-minion-master.zip
cd patch-minion-master/source
chmod +x setup.sh
./setup.sh


