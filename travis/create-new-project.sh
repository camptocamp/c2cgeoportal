#!/bin/bash -ex

WORKSPACE=$1
if [ $# -ge 2 ]
then
    PACKAGE=$2
else
    PACKAGE=testgeomapfishapp
fi
mkdir --parent ${WORKSPACE}/${PACKAGE}

if [ -z "$SCAFFOLDS" ]; then
    SCAFFOLDS="c2cgeoportal_create c2cgeoportal_update"
fi
if [ -z "$MAKEFILE" ]; then
    MAKEFILE="Makefile"
fi

DOCKER_RUN_ARGS="--env=SRID=21781 --env=EXTENT=489246.36,78873.44,837119.76,296543.14 --image=camptocamp/geomapfish-build --share=${WORKSPACE} ${DOCKER_RUN_ARGS}"
PCREATE_CMD="pcreate --ignore-conflicting-name --overwrite --package-name ${PACKAGE} ${WORKSPACE}/${PACKAGE}"
for s in $SCAFFOLDS
do
    ./docker-run ${DOCKER_RUN_ARGS} ${PCREATE_CMD} --scaffold=$s
done

# Copy files for travis build and tests
if [ $# -lt 2 ]
then
    cp travis/build.mk ${WORKSPACE}/${PACKAGE}/travis.mk
    cp travis/empty-vars.mk ${WORKSPACE}/${PACKAGE}/empty-vars.mk
    cp travis/vars.yaml ${WORKSPACE}/${PACKAGE}/vars_travis.yaml
    cp travis/docker-compose.yaml ${WORKSPACE}/${PACKAGE}/docker-compose.yaml
    cp travis/docker-compose-build.yaml ${WORKSPACE}/${PACKAGE}/docker-compose-build.yaml
    cp --recursive travis ${WORKSPACE}/${PACKAGE}/travis
fi
cd ${WORKSPACE}/${PACKAGE}
if [ $# -lt 2 ]
then
    echo no_external_network=true >> .config
fi

# Init Git repository
git init
git config user.email travis@camptocamp.com
git config user.name CI
if [ -z "`git remote -v | grep origin`" ]; then
git remote add origin . # add a fake remote
fi
if [ -n "`git diff --name-only`" ]; then
git add --all
git commit --quiet --message='Initial commit'
fi
git clean -fX

# Build
if [ $# -lt 2 ]
then
    ./docker-run make --makefile=travis.mk build
    ./docker-compose-run bash -c 'wait-db && PGHOST=externaldb PGDATABASE=test wait-db;'
    ./docker-compose-run make --makefile=travis.mk update-po
else
    ./docker-run --env=DOCKER_TAG=${MAJOR_VERSION} make -f $MAKEFILE build
fi
