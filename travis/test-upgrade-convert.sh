#!/bin/bash -ex

WORKSPACE=$2

DOCKER_RUN_ARGS="--env=SRID=21781 --env=APACHE_VHOST=test --env=EXTENT=489246.36,78873.44,837119.76,296543.14 --image=camptocamp/geomapfish-build"
PCREATE_ARGS="--ignore-conflicting-name --overwrite --package-name testgeomapfish"

export NODE_ENV=development

function pcreate {
    ./docker-run ${DOCKER_RUN_ARGS} $3 --share=$1 pcreate --scaffold=$2 $1/testgeomapfish ${PCREATE_ARGS}
}

function only_create {
    rm --recursive --force $1
    mkdir --parent $1
    pcreate $1 c2cgeoportal_create $2
    pcreate $1 c2cgeoportal_update $2
    cd $1/testgeomapfish
    git init
    git config user.email travis@camptocamp.com
    git config user.name CI
    git remote add origin . # add a fake remote
    cd -
}

function create {
    only_create $1 $2
    cd $1/testgeomapfish
    git add --all
    git commit --quiet --message="Initial commit"
    git clean -fX
    cd -
}


function printdiff {
    ls -l .UPGRADE*
    for f in $(ls -1 *.diff)
    do
        echo "--- $f ---"
        cat "$f"
    done
}

if [ "$1" = "init" ]
then
    rm --recursive --force ${WORKSPACE}/ref ${WORKSPACE}/v240  ${WORKSPACE}/v25
    rm --recursive --force $(find c2cgeoportal/scaffolds -name __pycache__)
    create ${WORKSPACE}/ref
    create ${WORKSPACE}/v25
    create ${WORKSPACE}/v240 --version=2.4.0
fi

if [ "$1" = "240" ]
then
    cd ${WORKSPACE}/240/testgeomapfish
    ./docker-run --env=NODE_ENV make upgrade
    if [ ! -e .UPGRADE_SUCCESS ]
    then
        printdiff
        echo "Fail to upgrade"
        exit 1
    fi
    ./docker-run make clean-all
    rm --recursive --force .UPGRADE9 .UPGRADE_SUCCESS \
        commons/testgeomapfish_commons.egg-info geoportal/testgeomapfish_geoportal.egg-info
    cd -
    find ${WORKSPACE}/docker -type d -empty -delete
    diff --recursive --exclude=.git ${WORKSPACE}/ref ${WORKSPACE}/240
fi

if [ "$1" = "25" ]
then
    cd ${WORKSPACE}/25/testgeomapfish
    ./docker-run --env=NODE_ENV make upgrade
    if [ ! -e .UPGRADE_SUCCESS ]
    then
        printdiff
        echo "Fail to upgrade"
        exit 1
    fi
    ./docker-run make clean-all
    rm --recursive --force .UPGRADE9 .UPGRADE_SUCCESS \
        commons/testgeomapfish_commons.egg-info geoportal/testgeomapfish_geoportal.egg-info
    cd -
    find ${WORKSPACE}/docker -type d -empty -delete
    diff --recursive --exclude=.git ${WORKSPACE}/ref ${WORKSPACE}/v25
fi


if [ "$1" = "cleanup" ]
then
    rm --recursive --force ${WORKSPACE}/ref ${WORKSPACE}/v240 ${WORKSPACE}/v25
fi
