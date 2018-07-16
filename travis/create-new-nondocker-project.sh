#!/bin/bash -ex

DOCKER_RUN_ARGS="--env=SRID=21781 --env=APACHE_VHOST=test --env=EXTENT=489246.36,78873.44,837119.76,296543.14 --image=camptocamp/geomapfish-build --share=/tmp/travis"
PCREATE_CMD="pcreate --overwrite --package-name testgeomapfish /tmp/travis/nondockertestgeomapfish"
./docker-run ${DOCKER_RUN_ARGS} ${PCREATE_CMD} --scaffold=c2cgeoportal_create
./docker-run ${DOCKER_RUN_ARGS} ${PCREATE_CMD} --scaffold=c2cgeoportal_nondockercreate
./docker-run ${DOCKER_RUN_ARGS} ${PCREATE_CMD} --scaffold=c2cgeoportal_update
./docker-run ${DOCKER_RUN_ARGS} ${PCREATE_CMD} --scaffold=c2cgeoportal_nondockerupdate

cp travis/build-nondocker.mk /tmp/travis/nondockertestgeomapfish/travis.mk
cp travis/vars-nondocker.yaml /tmp/travis/nondockertestgeomapfish/vars_travis.yaml
cp travis/empty-vars.mk /tmp/travis/nondockertestgeomapfish/
echo 'include testgeomapfish.mk' > /tmp/travis/nondockertestgeomapfish/Makefile
cp --recursive travis /tmp/travis/nondockertestgeomapfish/travis

export TRAVIS_FOLDER=$(pwd)
cd /tmp/travis/nondockertestgeomapfish

chmod +x CONST_create_template/deploy/hooks/*
chmod +x deploy/hooks/*

echo "REQUIREMENTS = --editable=${TRAVIS_FOLDER}" | cat - travis.mk > travis.mk.new
mv travis.mk.new travis.mk

# init Git repository
git init
git config user.email travis@camptocamp.com
git config user.name CI
git remote add origin . # add a fake remote
git add --all
git commit --quiet --message="Initial commit"
git clean -fX

sudo chmod g+w,o+w /etc/apache2/sites-enabled/
sudo chmod 777 /var/lib/tomcat7/webapps

sudo a2enmod headers
sudo a2enmod rewrite
sudo a2enmod fcgid

# Minimal build
./docker-run make --makefile=travis.mk \
    build \
    geoportal/alembic.ini \
    geoportal/alembic.yaml \
    geoportal/production.ini \
    geoportal/config.yaml \
    docker-compose-build.yaml docker-build-testdb
FINALISE=TRUE make --makefile=travis.mk build
DOCKER_RUN_ALEMBIC="./docker-run --env=PGSCHEMA=main --env=PGSCHEMA_STATIC=main_static alembic"
${DOCKER_RUN_ALEMBIC} --config=geoportal/alembic.ini --name=main upgrade head
${DOCKER_RUN_ALEMBIC} --config=geoportal/alembic.ini --name=static upgrade head
# Create default theme
./docker-run /build/venv/bin/python /usr/local/bin/create-demo-theme --iniconfig geoportal/production.ini
./docker-run make --makefile=travis.mk update-po
git add geoportal/testgeomapfish_geoportal/locale/*/LC_MESSAGES/*.po
git commit -m "Add initial localisation"
./docker-run make --makefile=travis.mk theme2fts
