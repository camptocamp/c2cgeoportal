#!/bin/bash -ex

sudo a2enmod headers
sudo a2enmod rewrite
sudo a2enmod wsgi
sudo /usr/sbin/apachectl restart
sudo chmod g+w,o+w /etc/apache2/sites-enabled/

cp travis/build.mk /tmp/testgeomapfish/travis.mk

cd /tmp/testgeomapfish/

sed -e 's@^c2cgeoportal==.*$@/home/travis/build/camptocamp/c2cgeoportal@' -i CONST_requirements.txt

git config --global user.name "Travis"
git config --global user.email "travis@example.com"
git init
git add -A
git submodule add https://github.com/camptocamp/cgxp.git testgeomapfish/static/lib/cgxp
git commit -q -m "Initial commit"

sudo chmod 777 /var/lib/tomcat7/webapps

make -f travis.mk cleanall

sudo -u postgres psql -c 'GRANT SELECT ON TABLE spatial_ref_sys TO "www-data"' geomapfish
sudo -u postgres psql -c 'GRANT ALL ON TABLE geometry_columns TO "www-data"' geomapfish
sudo -u postgres psql -c "CREATE SCHEMA main;" geomapfish
sudo -u postgres psql -c "CREATE SCHEMA main_static;" geomapfish
sudo -u postgres psql -c 'GRANT ALL ON SCHEMA main TO "www-data"' geomapfish
sudo -u postgres psql -c 'GRANT ALL ON SCHEMA main_static TO "www-data"' geomapfish
make -f travis.mk .build/requirements.timestamp alembic.ini alembic_static.ini
.build/venv/bin/alembic -c alembic.ini upgrade head
.build/venv/bin/alembic -c alembic_static.ini upgrade head

make -f travis.mk build

echo "Build complete"

git add testgeomapfish/locale/*/LC_MESSAGES/testgeomapfish-server.po
git commit -m "Add location"

cd -
