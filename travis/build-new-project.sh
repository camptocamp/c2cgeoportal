#!/bin/bash -ex

cp travis/build.mk /tmp/test/travis.mk

cd /tmp/test/
mkdir print/print-app

git config --global user.name "Travis"
git config --global user.email "travis@example.com"
git init
git add -A
git submodule add https://github.com/camptocamp/cgxp.git test/static/lib/cgxp
git commit -q -m "Initial commit"

sudo chmod 777 /var/lib/tomcat7/webapps

make -f travis.mk build

echo "Build complete"

git add test/locale/*/LC_MESSAGES/test-server.po
git commit -m "Add location"

sudo -u postgres psql -c 'GRANT SELECT ON TABLE spatial_ref_sys TO "www-data"' geomapfish
sudo -u postgres psql -c 'GRANT ALL ON TABLE geometry_columns TO "www-data"' geomapfish
sudo -u postgres psql -c "CREATE SCHEMA main;" geomapfish
sudo -u postgres psql -c "CREATE SCHEMA main_static;" geomapfish
sudo -u postgres psql -c 'GRANT ALL ON SCHEMA main TO "www-data"' geomapfish
sudo -u postgres psql -c 'GRANT ALL ON SCHEMA main_static TO "www-data"' geomapfish

.build/venv/bin/alembic upgrade head

sudo touch /etc/apache2/sites-enabled/test.conf
sudo chmod 666 /etc/apache2/sites-enabled/test.conf
echo "Include /tmp/test/apache/*.conf" > /etc/apache2/sites-enabled/test.conf

sudo a2enmod headers
sudo a2enmod rewrite
sudo a2enmod wsgi
sudo /usr/sbin/apachectl restart

cd -
