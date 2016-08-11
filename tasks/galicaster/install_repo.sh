#!/bin/bash

echo "deb https://packages.galicaster.org/apt xenial main" | sudo tee --append /etc/apt/sources.list.d/galicaster.list 
wget -O - https://packages.galicaster.org/apt/galicaster.gpg.key | sudo apt-key add -
