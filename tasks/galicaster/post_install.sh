#!/bin/bash

mkdir -p /usr/share/galicaster-repository
mkdir -p /var/logs/galicaster

sudo groupadd galicaster
sudo usermod -aG galicaster galicaster

chown -R galicaster:galicaster /usr/share/galicaster
chown -R galicaster:galicaster /usr/share/galicaster-repository
chown -R galicaster:galicaster /var/logs/galicaster
chown -R galicaster:galicaster /etc/galicaster
