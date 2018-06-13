#!/bin/bash -ex

WORKSPACE=$1
mkdir --parent ${WORKSPACE}/testgeomapfish

export SRID=21781 EXTENT=489246.36,78873.44,837119.76,296543.14
./docker-run --image=camptocamp/geomapfish-build --share ${WORKSPACE} pcreate --scaffold=c2cgeoportal_create \
    --ignore-conflicting-name --package-name testgeomapfish ${WORKSPACE}/testgeomapfish
./docker-run --image=camptocamp/geomapfish-build --share ${WORKSPACE} pcreate --scaffold=c2cgeoportal_update \
    --ignore-conflicting-name --package-name testgeomapfish ${WORKSPACE}/testgeomapfish

# Copy files for travis build and tests
cp travis/build.mk ${WORKSPACE}/testgeomapfish/travis.mk
cp travis/empty-vars.mk ${WORKSPACE}/testgeomapfish/empty-vars.mk
cp travis/vars.yaml ${WORKSPACE}/testgeomapfish/vars_travis.yaml
cp travis/docker-compose.yaml.mako ${WORKSPACE}/testgeomapfish/docker-compose.yaml.mako
cp travis/docker-compose-build.yaml.mako ${WORKSPACE}/testgeomapfish/docker-compose-build.yaml.mako
cp --recursive travis ${WORKSPACE}/testgeomapfish/travis
cd ${WORKSPACE}/testgeomapfish

# Init Git repository
git init
git config user.email travis@camptocamp.com
git config user.name CI
git remote add origin . # add a fake remote
git add --all
git commit --quiet --message='Initial commit'
git clean -fX

# Build
./docker-run make --makefile=travis.mk build docker-build-testdb
./docker-compose-run make --makefile=travis.mk update-po
./docker-compose-run make --makefile=travis.mk theme2fts
