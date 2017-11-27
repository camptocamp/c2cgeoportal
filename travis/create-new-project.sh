#!/bin/bash -ex

WORKSPACE=$1
./docker-run --image=camptocamp/geomapfish-build make clean-all
mkdir --parent ${WORKSPACE}/testgeomapfish

export SRID=21781 EXTENT=489246.36,78873.44,837119.76,296543.14
./docker-run --image=camptocamp/geomapfish-build --share ${WORKSPACE} pcreate --scaffold=c2cgeoportal_create \
    --ignore-conflicting-name --package-name testgeomapfish ${WORKSPACE}/testgeomapfish
./docker-run --image=camptocamp/geomapfish-build --share ${WORKSPACE} pcreate --scaffold=c2cgeoportal_update \
    --ignore-conflicting-name --package-name testgeomapfish ${WORKSPACE}/testgeomapfish
./docker-run --image=camptocamp/geomapfish-build --share ${WORKSPACE} pcreate --scaffold=tilecloud_chain \
    ${WORKSPACE}/testgeomapfish

# Copy files for travis build and tests
cp travis/build.mk ${WORKSPACE}/testgeomapfish/travis.mk
cp travis/empty-vars.mk ${WORKSPACE}/testgeomapfish/empty-vars.mk
cp travis/vars.yaml ${WORKSPACE}/testgeomapfish/vars_travis.yaml
cp travis/docker-compose.yaml ${WORKSPACE}/testgeomapfish/docker-compose.yaml.mako
cp --recursive travis ${WORKSPACE}/testgeomapfish/travis
cd ${WORKSPACE}/testgeomapfish

# Init Git repository
git init
git add --all
git commit --quiet --message="Initial commit"
git remote add origin . # add a fake remote

# Minimal build
./docker-run make --makefile=travis.mk \
    docker-compose-build.yaml \
    geoportal-docker mapserver-docker print-docker testdb-docker
# Wait DB
./docker-compose-run sleep 15
# Create default theme
./docker-compose-run create-demo-theme
