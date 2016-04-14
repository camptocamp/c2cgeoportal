#!/bin/bash -ex

.build/venv/bin/pcreate -s c2cgeoportal_create /tmp/travis/testgeomapfish package=testgeomapfish srid=21781 mobile_application_title="Mobile App éàè" apache_vhost=test extent= > /dev/null
.build/venv/bin/pcreate -s c2cgeoportal_update /tmp/travis/testgeomapfish package=testgeomapfish srid=21781 mobile_application_title="Mobile App éàè" apache_vhost=test > /dev/null # on create

cp travis/build.mk /tmp/travis/testgeomapfish/travis.mk
cp travis/vars.yaml /tmp/travis/testgeomapfish/vars_travis.yaml
cd /tmp/travis/testgeomapfish

echo "REQUIREMENTS = -e ${TRAVIS_FOLDER}" | cat - travis.mk > travis.mk.new
mv travis.mk.new travis.mk

# init Git repository
git config --global user.name "Travis"
git config --global user.email "travis@example.com"
git init
git add -A
git submodule add https://github.com/camptocamp/cgxp.git testgeomapfish/static/lib/cgxp
git commit -qm "Initial commit"
git remote add origin . # add a fake remote

sudo chmod g+w,o+w /etc/apache2/sites-enabled/
sudo chmod 777 /var/lib/tomcat7/webapps

sudo a2enmod headers
sudo a2enmod rewrite
sudo a2enmod wsgi
sudo a2enmod fcgid

sudo -u postgres psql -c 'GRANT SELECT ON TABLE spatial_ref_sys TO "www-data"' geomapfish
sudo -u postgres psql -c 'GRANT ALL ON TABLE geometry_columns TO "www-data"' geomapfish
sudo -u postgres psql -c "CREATE SCHEMA main;" geomapfish
sudo -u postgres psql -c "CREATE SCHEMA main_static;" geomapfish
sudo -u postgres psql -c 'GRANT ALL ON SCHEMA main TO "www-data"' geomapfish
sudo -u postgres psql -c 'GRANT ALL ON SCHEMA main_static TO "www-data"' geomapfish

make -f travis.mk .build/requirements.timestamp alembic.ini alembic_static.ini
.build/venv/bin/alembic -c alembic.ini upgrade head
.build/venv/bin/alembic -c alembic_static.ini upgrade head
