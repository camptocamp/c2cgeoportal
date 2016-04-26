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
# Alias /c2cgeoportal "/var/www/vhosts/docs.camptocamp.net/htdocs/c2cgeoportal/html"
# <Directory "/var/www/vhosts/docs.camptocamp.net/htdocs/c2cgeoportal/html">
#     Options Indexes FollowSymLinks MultiViews
#     AllowOverride None
#     Order allow,deny
#     allow from all
# </Directory>
#

BUILDBASEDIR=/var/www/vhosts/docs.camptocamp.net/htdocs/c2cgeoportal

git fetch

VERSION = 1.6

# BUILDDIR is where the HTML files are generated
BUILDDIR=${BUILDBASEDIR}/${VERSION}

# create the build dir if it doesn't exist
if [[ ! -d ${BUILDDIR} ]]; then
    mkdir -p ${BUILDDIR}
fi

# reset local changes and get the latest files
git clean -f -d
git reset --hard origin/${VERSION}

# create a virtual env if none exists already
if [[ ! -d env ]]; then
    virtualenv env
fi

# install or update Sphinx
if [ -e requirements.txt ]
then
    ./env/bin/pip install -r requirements.txt
else
    ./env/bin/pip install Sphinx==1.1.3 sphinx-prompt==0.2.2
fi

make SPHINXBUILD=./env/bin/sphinx-build BUILDDIR=${BUILDDIR} clean html

if [ ! -e ${BUILDBASEDIR}/html/${VERSION} ]; then
    ln -s ${BUILDBASEDIR}/${VERSION}/html ${BUILDBASEDIR}/html/${VERSION}
fi
