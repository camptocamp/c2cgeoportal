#!/bin/bash

#
# This script updates the c2cgeoportal HTML docs available at 
# http://docs.camptocamp.net/c2cgeoportal/ 
#
# This script is to be run on the doc.camptocamp.net server,
# from the c2cgeoportal/doc directory.
#
# To run the script change dir to c2cgeoportal/doc and do:
#   ./update_online.sh
#
# Possible Apache config:
#
# Alias /c2cgeoportal "/var/www/docs.camptocamp.net/htdocs/c2cgeoportal/html"
# <Directory "/var/www/docs.camptocamp.net/htdocs/c2cgeoportal/html">
#     Options Indexes FollowSymLinks MultiViews
#     AllowOverride None
#     Order allow,deny
#     allow from all
# </Directory>
#

# BUILDDIR is where the HTML files are generated
BUILDDIR=/var/www/docs.camptocamp.net/htdocs/c2cgeoportal

# create the build dir if it doesn't exist
if [[ ! -d ${BUILDDIR} ]]; then
    mkdir -p ${BUILDDIR}
fi

# get the latest files
svn up

# create a virtual env if none exists already
if [[ ! -d env ]]; then
    curl http://mapfish.org/downloads/virtualenv-1.4.5.py | python - --no-site-packages --distribute env
fi

# install or update Sphinx
./env/bin/pip install 'Sphinx==1.1.2'

make SPHINXBUILD=./env/bin/sphinx-build BUILDDIR=${BUILDDIR} clean html

exit 0
