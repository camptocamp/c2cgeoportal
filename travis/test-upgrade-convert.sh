#!/bin/bash -ex

WORKSPACE=$2

function pcreate {
    ./docker-run --image=camptocamp/geomapfish-build --share $1 pcreate --scaffold=$2 $1/testgeomapfish \
        --overwrite --ignore-conflicting-name --package-name testgeomapfish
}

function create {
    rm --recursive --force $1
    mkdir --parent $1
    pcreate $1 c2cgeoportal_create
    pcreate $1 c2cgeoportal_update
    pcreate $1 tilecloud_chain
    cd $1/testgeomapfish
    git init
    git remote add origin . # add a fake remote
    git add --all
    git commit --quiet --message="Initial commit"
    rm .upgrade.yaml
    rm --recursive --force $(find -name __pycache__)
    cd -
}

function createnondocker {
    create $1
    pcreate $1 c2cgeoportal_nondockercreate
    pcreate $1 c2cgeoportal_nondockerupdate
    cd $1/testgeomapfish
    git add --all
    git commit --quiet --message="Initial commit"
    rm .upgrade.yaml
    rm --recursive --force $(find -name __pycache__)
    cd -
}

function createv220 {
    rm --recursive --force $1
    mkdir --parent $1
    cp --recursive ${WORKSPACE}/v220/testgeomapfish $1/testgeomapfish
    pcreate $1 tilecloud_chain
    cd $1/testgeomapfish
    git init
    git remote add origin . # add a fake remote
    git add --all
    git commit --quiet --message="Initial commit"
    cd -
}

if [ "$1" = "init" ]
then
    rm --recursive --force ${WORKSPACE}/nondockerref ${WORKSPACE}/dockerref \
        ${WORKSPACE}/nondocker ${WORKSPACE}/docker \
        ${WORKSPACE}/v220-todocker ${WORKSPACE}/v220-tonondocker \
        ${WORKSPACE}/testgeomapfish
    rm --recursive --force $(find c2cgeoportal/scaffolds -name __pycache__)
    export SRID=21781 APACHE_VHOST=test EXTENT=489246.36,78873.44,837119.76,296543.14
    create ${WORKSPACE}/docker
    create ${WORKSPACE}/dockerref
    createnondocker ${WORKSPACE}/nondocker
    createnondocker ${WORKSPACE}/nondockerref
    unset SRID APACHE_VHOST EXTENT
    mkdir --parent ${WORKSPACE}/v220
    ./docker-run --share=${WORKSPACE} tar --extract  --bzip2 --file=travis/v220.tar.bz2  --directory=${WORKSPACE}/v220
    createv220 ${WORKSPACE}/v220-todocker
    createv220 ${WORKSPACE}/v220-tonondocker
fi

if [ "$1" = "docker" ]
then
    cd ${WORKSPACE}/docker/testgeomapfish
    ./docker-run make upgrade
    if [ ! -e .UPGRADE_SUCCESS ]
    then
        echo "Fail to upgrade"
        exit 1
    fi
    ./docker-run make clean-all
    rm --recursive --force .UPGRADE10 .UPGRADE_SUCCESS \
        commons/testgeomapfish_commons.egg-info geoportal/testgeomapfish_geoportal.egg-info
    cd -
    diff --recursive --exclude=.git ${WORKSPACE}/dockerref ${WORKSPACE}/docker
fi

if [ "$1" = "nondocker" ]
then
    cd ${WORKSPACE}/nondocker/testgeomapfish
    ./docker-run make --makefile=testgeomapfish.mk upgrade
    if [ ! -e .UPGRADE_SUCCESS ]
    then
        echo "Fail to upgrade"
        exit 1
    fi
    ./docker-run make --makefile=testgeomapfish.mk clean-all
    rm --recursive --force .UPGRADE10 .UPGRADE_SUCCESS \
        commons/testgeomapfish_commons.egg-info geoportal/testgeomapfish_geoportal.egg-info
    cd -
    diff --recursive --exclude=.git ${WORKSPACE}/nondockerref ${WORKSPACE}/nondocker
fi

if [ "$1" = "todocker" ]
then
    cd ${WORKSPACE}/nondocker/testgeomapfish
    echo "UPGRADE_ARGS += --force-docker --new-makefile=Makefile" > temp.mk
    cat testgeomapfish.mk >> temp.mk
    git rm testgeomapfish.mk
    git add temp.mk
    git commit --quiet --message="Start upgrade"
    ./docker-run make --makefile=temp.mk upgrade
    if [ ! -e .UPGRADE7 ]
    then
        echo "Fail to upgrade"
        exit 1
    fi
    cp {CONST_create_template/,}project.yaml.mako
    cp {CONST_create_template/,}mapserver/tinyows.xml.mako
    cp {CONST_create_template/,}print/print-apps/testgeomapfish/config.yaml.mako
    ./docker-run make upgrade8
    if [ ! -e .UPGRADE_SUCCESS ]
    then
        echo "Fail to upgrade"
        exit 1
    fi
    git rm temp.mk
    ./docker-run make clean-all
    rm --recursive --force .UPGRADE10 .UPGRADE_SUCCESS \
        commons/testgeomapfish_commons.egg-info geoportal/testgeomapfish_geoportal.egg-info
    cd -
    diff --recursive --exclude=.git ${WORKSPACE}/dockerref ${WORKSPACE}/nondocker
fi

if [ "$1" = "tonondocker" ]
then
    cd ${WORKSPACE}/docker/testgeomapfish
    cp Makefile tmp
    echo "UPGRADE_ARGS += --nondocker --new-makefile=testgeomapfish.mk" > Makefile
    cat tmp >> Makefile
    rm tmp
    git add Makefile
    git commit --quiet --message="Start upgrade"
    export APACHE_VHOST=test
    ./docker-run make upgrade
    if [ ! -e .UPGRADE7 ]
    then
        echo "Fail to upgrade"
        exit 1
    fi
    cp {CONST_create_template/,}project.yaml.mako
    cp {CONST_create_template/,}testgeomapfish.mk
    cp {CONST_create_template/,}mapserver/tinyows.xml.mako
    cp {CONST_create_template/,}print/print-apps/testgeomapfish/config.yaml.mako
    ./docker-run make --makefile=testgeomapfish.mk upgrade8
    if [ ! -e .UPGRADE_SUCCESS ]
    then
        echo "Fail to upgrade"
        exit 1
    fi
    ./docker-run make --makefile=testgeomapfish.mk clean-all
    rm --recursive --force .UPGRADE10 .UPGRADE_SUCCESS \
        commons/testgeomapfish_commons.egg-info geoportal/testgeomapfish_geoportal.egg-info
    cd -
    diff --recursive --exclude=.git ${WORKSPACE}/nondockerref ${WORKSPACE}/docker
fi

function v220 {
    cp docker-run $1/testgeomapfish
    cp travis/v22-project.yaml $1/testgeomapfish/project.yaml.mako
    cd $1/testgeomapfish
    head --lines=-23 CONST_vars.yaml > CONST_vars.yaml_
    mv CONST_vars.yaml{_,}
    git add docker-run project.yaml.mako CONST_vars.yaml
    git commit --quiet --message="Start upgrade"
    ./docker-run c2c-template --vars vars_testgeomapfish.yaml --engine mako --files project.yaml.mako
    if [ "$2" == non ]
    then
        ./docker-run --image=camptocamp/geomapfish-build \
            c2cupgrade --nondocker --makefile=testgeomapfish.mk
        MAKE_ARGS=--makefile=testgeomapfish.mk
    else
        ./docker-run --image=camptocamp/geomapfish-build \
            c2cupgrade --force-docker --new-makefile=Makefile --makefile=testgeomapfish.mk
    fi
    if [ ! -e .UPGRADE6 ]
    then
        echo "Fail to upgrade"
        exit 1
    fi
    ./docker-run make $MAKE_ARGS upgrade7
    if [ "$2" == non ]
    then
        if [ ! -e .UPGRADE7 ]
        then
            echo "Fail to upgrade"
            exit 1
        fi
        ./docker-run make $MAKE_ARGS upgrade8
    fi
    if [ ! -e .UPGRADE8 ]
    then
        echo "Fail to upgrade"
        exit 1
    fi
    ./docker-run make $MAKE_ARGS upgrade9
    if [ ! -e .UPGRADE_SUCCESS ]
    then
        echo "Fail to upgrade"
        exit 1
    fi
    ./docker-run make $MAKE_ARGS clean-all
    rm --recursive --force .UPGRADE10 .UPGRADE_SUCCESS \
        commons/testgeomapfish_commons.egg-info geoportal/testgeomapfish_geoportal.egg-info
    cd -
    diff --recursive --exclude=.git --exclude=LC_MESSAGES ${WORKSPACE}/$2dockerref $1
}

if [ "$1" = "v220-todocker" ]
then
    v220 ${WORKSPACE}/v220-todocker
fi

if [ "$1" = "v220-tonondocker" ]
then
    v220 ${WORKSPACE}/v220-tonondocker non
fi

if [ "$1" = "cleanup" ]
then
    rm --recursive --force ${WORKSPACE}/nondockerref ${WORKSPACE}/dockerref \
        ${WORKSPACE}/nondocker ${WORKSPACE}/docker \
        ${WORKSPACE}/v220-todocker ${WORKSPACE}/v220-tonondocker \
        ${WORKSPACE}/testgeomapfish
fi
