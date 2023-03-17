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

function createnondocker {
    only_create $1 $2
    pcreate $1 c2cgeoportal_nondockercreate $2
    pcreate $1 c2cgeoportal_nondockerupdate $2
    cd $1/testgeomapfish
    git add --all
    git commit --quiet --message="Initial commit"
    git clean -fX
    cd -
}

function printdiff {
    ls -l .UPGRADE*
    for f in $(ls -1 *.diff); do
        echo "--- $f ---"
        cat "$f"
    done
}

if [ "$1" = "init" ]; then
    rm --recursive --force ${WORKSPACE}/dockerref \
        ${WORKSPACE}/nondocker ${WORKSPACE}/docker \
        ${WORKSPACE}/testgeomapfish
    rm --recursive --force $(find c2cgeoportal/scaffolds -name __pycache__)
    create ${WORKSPACE}/docker
    create ${WORKSPACE}/dockerref
    createnondocker ${WORKSPACE}/nondocker
    create ${WORKSPACE}/v240 --version=2.4.1
fi

if [ "$1" = "docker" ]; then
    cd ${WORKSPACE}/docker/testgeomapfish
    ./docker-run --env=NODE_ENV make upgrade
    if [ ! -e .UPGRADE_SUCCESS ]; then
        printdiff
        echo "Fail to upgrade"
        exit 1
    fi
    ./docker-run make clean-all
    rm --recursive --force .UPGRADE9 .UPGRADE_SUCCESS \
        commons/testgeomapfish_commons.egg-info geoportal/testgeomapfish_geoportal.egg-info
    cd -
    find ${WORKSPACE}/docker -type d -empty -delete
    diff --recursive --exclude=.git ${WORKSPACE}/dockerref ${WORKSPACE}/docker
fi

if [ "$1" = "todocker" ]; then
    cp travis/v24-project.yaml ${WORKSPACE}/nondocker/testgeomapfish/project.yaml.mako
    cd ${WORKSPACE}/nondocker/testgeomapfish
    echo "UPGRADE_ARGS += --force-docker --new-makefile=Makefile" > temp.mk
    cat testgeomapfish.mk >> temp.mk
    git rm testgeomapfish.mk
    git add temp.mk project.yaml.mako
    git commit --quiet --message="Start upgrade"
    ./docker-run --env=NODE_ENV make --makefile=temp.mk upgrade
    ./docker-run make --always-make --makefile=CONST_convert2tmpl.mk to-tmpl
    cp {CONST_create_template/,}project.yaml.mako
    cp {CONST_create_template/,}vars.yaml
    cp {CONST_create_template/,}mapserver/tinyows.xml.tmpl
    cp {CONST_create_template/,}print/print-apps/testgeomapfish/config.yaml.tmpl
    cp {CONST_create_template/,}.env.mako
    cp {CONST_create_template/,}docker-compose.yaml
    cp {CONST_create_template/,}tilegeneration/config.yaml.tmpl
    cp CONST_create_template/mapserver/*.tmpl mapserver
    if [ -e .UPGRADE10 ]; then
        ./docker-run --env=NODE_ENV make upgrade11
    fi
    if [ ! -e .UPGRADE_SUCCESS ]; then
        printdiff
        echo "Fail to upgrade"
        exit 1
    fi
    git rm temp.mk
    ./docker-run make clean-all
    rm --recursive --force .UPGRADE11 .UPGRADE_SUCCESS \
        commons/testgeomapfish_commons.egg-info geoportal/testgeomapfish_geoportal.egg-info
    cd -
    find ${WORKSPACE}/nondocker -type d -empty -delete
    diff --recursive --exclude=.git ${WORKSPACE}/dockerref ${WORKSPACE}/nondocker
fi

function v240 {
    cp travis/from23-config ${WORKSPACE}/v240/testgeomapfish/.config
    cd ${WORKSPACE}/v240/testgeomapfish
    ./docker-run make project.yaml
    git add project.yaml.mako .config
    git commit --quiet --message="Start upgrade"
    ./docker-run --env=NODE_ENV make upgrade
    ./docker-run make --always-make --makefile=CONST_convert2tmpl.mk to-tmpl
    if [ -e .UPGRADE8 ]; then
        cat changelog.diff
        ./docker-run --env=NODE_ENV make upgrade9
    fi
    if [ -e .UPGRADE9 ]; then
        git apply --3way ngeo.diff
        ./docker-run --env=NODE_ENV make upgrade10
    fi
    if [ -e .UPGRADE10 ]; then
        git apply --3way create.diff
        ./docker-run --env=NODE_ENV make upgrade11
    fi
    if [ ! -e .UPGRADE_SUCCESS ]; then
        printdiff
        echo "Fail to upgrade"
        exit 1
    fi
    ./docker-run make clean-all
    rm --recursive --force .UPGRADE* \
        commons/testgeomapfish_commons.egg-info geoportal/testgeomapfish_geoportal.egg-info
    cd -
    find ${WORKSPACE}/v240 -type d -empty -delete
    diff --recursive --exclude=.git --exclude=locale ${WORKSPACE}/$1dockerref ${WORKSPACE}/v240
}

if [ "$1" = "v240" ]; then
    v240
fi

if [ "$1" = "cleanup" ]; then
    rm --recursive --force ${WORKSPACE}/dockerref \
        ${WORKSPACE}/nondocker ${WORKSPACE}/docker
fi
