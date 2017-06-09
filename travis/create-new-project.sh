#!/bin/bash -ex

export SRID=21781 APACHE_VHOST=test EXTENT=489246.36,78873.44,837119.76,296543.14
./docker-run pcreate --scaffold=c2cgeoportal_create /tmp/travis/testgeomapfish --package-name testgeomapfish > /dev/null
./docker-run pcreate --scaffold=c2cgeoportal_update /tmp/travis/testgeomapfish --package-name testgeomapfish > /dev/null # on create

cp travis/build.mk /tmp/travis/testgeomapfish/travis.mk
cp travis/vars.yaml /tmp/travis/testgeomapfish/vars_travis.yaml
cd /tmp/travis/testgeomapfish

chmod +x CONST_create_template/deploy/hooks/*
chmod +x deploy/hooks/*

echo "REQUIREMENTS = --editable ${TRAVIS_FOLDER}" | cat - travis.mk > travis.mk.new
mv travis.mk.new travis.mk

# init Git repository
git config --global user.name "Travis"
git config --global user.email "travis@example.com"
git init
git add --all
git submodule add https://github.com/camptocamp/cgxp.git testgeomapfish/static/lib/cgxp
git commit --quiet --message="Initial commit"
git remote add origin . # add a fake remote

sudo chmod g+w,o+w /etc/apache2/sites-enabled/
sudo chmod 777 /var/lib/tomcat7/webapps

sudo a2enmod headers
sudo a2enmod rewrite
sudo a2enmod wsgi
sudo a2enmod fcgid

make -f travis.mk .build/requirements.timestamp alembic.ini alembic_static.ini production.ini .build/config.yaml .build/venv/bin/alembic
.build/venv/bin/alembic --config alembic.ini upgrade head
.build/venv/bin/alembic --config alembic_static.ini upgrade head
.build/venv/bin/create-demo-theme
