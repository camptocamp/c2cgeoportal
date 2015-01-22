#!/bin/bash -e

cp travis/build.mk /tmp/test/travis.mk

cd /tmp/test/
mkdir print/print-app

git init
git submodule add https://github.com/camptocamp/cgxp.git test/static/lib/cgxp

sudo mkdir -p /srv/tomcat/tomcat1/webapps/
sudo chmod 777 /srv/tomcat/tomcat1/webapps/

make -f travis.mk build

echo "Build complete"

sudo touch /etc/apache2/sites-enabled/test.conf
sudo chmod 666 /etc/apache2/sites-enabled/test.conf
echo "Include /tmp/test/apache/*.conf" > /etc/apache2/sites-enabled/test.conf

sudo a2enmod headers
sudo a2enmod rewrite
sudo a2enmod wsgi
sudo /usr/sbin/apachectl restart

cd -
