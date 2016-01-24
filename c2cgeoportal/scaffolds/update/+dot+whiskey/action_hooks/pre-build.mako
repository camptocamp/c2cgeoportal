#!/usr/bin/env bash
#Script executed while creating the WSGI docker container, just before doing pip install
set -e

apt-get update
apt-get install -y libpq-dev libgeos-dev libproj-dev libjpeg-dev
rm -r /var/lib/apt/lists/*

mkdir -p `dirname "${directory}"`
ln -s "$PWD" "${directory}"
