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

function createv220 {
    rm --recursive --force $1
    mkdir --parent $1
    cp --recursive ${WORKSPACE}/v220/testgeomapfish $1/testgeomapfish
    cd $1/testgeomapfish
    git init
    git config user.email travis@camptocamp.com
    git config user.name CI
    git remote add origin . # add a fake remote
    git add --all
    git commit --quiet --message="Initial commit"
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
    rm --recursive --force ${WORKSPACE}/nondockerref ${WORKSPACE}/dockerref \
        ${WORKSPACE}/nondocker ${WORKSPACE}/docker \
        ${WORKSPACE}/v220-todocker ${WORKSPACE}/v220-tonondocker \
        ${WORKSPACE}/testgeomapfish
    rm --recursive --force $(find c2cgeoportal/scaffolds -name __pycache__)
    create ${WORKSPACE}/docker
    create ${WORKSPACE}/dockerref
    createnondocker ${WORKSPACE}/nondocker
    createnondocker ${WORKSPACE}/nondockerref
    create ${WORKSPACE}/v230-docker --version=2.3.1
    createnondocker ${WORKSPACE}/v230-nondocker --version=2.3.1
    mkdir --parent ${WORKSPACE}/v220
    ./docker-run --share=${WORKSPACE} tar --extract  --bzip2 --file=travis/v220.tar.bz2  --directory=${WORKSPACE}/v220
    createv220 ${WORKSPACE}/v220-todocker
    createv220 ${WORKSPACE}/v220-tonondocker
fi

if [ "$1" = "docker" ]
then
    cd ${WORKSPACE}/docker/testgeomapfish
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
    diff --recursive --exclude=.git ${WORKSPACE}/dockerref ${WORKSPACE}/docker
fi

if [ "$1" = "nondocker" ]
then
    cd ${WORKSPACE}/nondocker/testgeomapfish
    ./docker-run --env=NODE_ENV make --makefile=testgeomapfish.mk upgrade
    if [ ! -e .UPGRADE_SUCCESS ]
    then
        printdiff
        echo "Fail to upgrade"
        exit 1
    fi
    ./docker-run make --makefile=testgeomapfish.mk clean-all
    rm --recursive --force .UPGRADE9 .UPGRADE_SUCCESS \
        commons/testgeomapfish_commons.egg-info geoportal/testgeomapfish_geoportal.egg-info
    cd -
    find ${WORKSPACE}/nondocker -type d -empty -delete
    diff --recursive --exclude=.git ${WORKSPACE}/nondockerref ${WORKSPACE}/nondocker
fi

if [ "$1" = "todocker" ]
then
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
    if [ -e .UPGRADE10 ]
    then
        ./docker-run --env=NODE_ENV make upgrade11
    fi
    if [ ! -e .UPGRADE_SUCCESS ]
    then
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

if [ "$1" = "tonondocker" ]
then
    cp travis/v24-project.yaml ${WORKSPACE}/docker/testgeomapfish/project.yaml.mako
    cd ${WORKSPACE}/docker/testgeomapfish
    cp Makefile tmp
    echo "UPGRADE_ARGS += --nondocker --new-makefile=testgeomapfish.mk" > Makefile
    cat tmp >> Makefile
    rm tmp
    git add Makefile project.yaml.mako
    git commit --quiet --message="Start upgrade"
    export APACHE_VHOST=test
    ./docker-run --env=NODE_ENV make upgrade
    cp {CONST_create_template/,}project.yaml.mako
    cp {CONST_create_template/,}vars.yaml
    cp {CONST_create_template/,}testgeomapfish.mk
    cp {CONST_create_template/,}mapserver/tinyows.xml.mako
    cp {CONST_create_template/,}print/print-apps/testgeomapfish/config.yaml.mako
    if [ -e .UPGRADE10 ]
    then
        ./docker-run --env=NODE_ENV make --makefile=testgeomapfish.mk upgrade11
    fi
    if [ ! -e .UPGRADE_SUCCESS ]
    then
        printdiff
        echo "Fail to upgrade"
        exit 1
    fi
    ./docker-run make --makefile=testgeomapfish.mk clean-all
    rm --recursive --force .UPGRADE11 .UPGRADE_SUCCESS \
        commons/testgeomapfish_commons.egg-info geoportal/testgeomapfish_geoportal.egg-info
    cd -
    find ${WORKSPACE}/docker -type d -empty -delete
    diff --recursive --exclude=.git ${WORKSPACE}/nondockerref ${WORKSPACE}/docker
fi

function v220 {
    cp docker-run $1/testgeomapfish
    cp travis/old-project.yaml $1/testgeomapfish/project.yaml.mako
    cd $1/testgeomapfish
    head --lines=-23 CONST_vars.yaml > CONST_vars.yaml_
    mv CONST_vars.yaml{_,}
    echo 'no_interpreted: [reset_password.email_body]' >> CONST_vars.yaml
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
    if [ ! -e .UPGRADE8 ]
    then
        printdiff
        echo "Fail to upgrade"
        exit 1
    fi
    mv geoportal/testgeomapfish_geoportal/locale/en/LC_MESSAGES/testgeomapfish{,_geoportal}-client.po
    mv geoportal/testgeomapfish_geoportal/locale/fr/LC_MESSAGES/testgeomapfish{,_geoportal}-client.po
    mv geoportal/testgeomapfish_geoportal/locale/de/LC_MESSAGES/testgeomapfish{,_geoportal}-client.po
    if [ "$2" != non ]
    then
        cp CONST_create_template/docker-compose.yaml .
        cp CONST_create_template/.env.mako .
        ./docker-run make --always-make --makefile=CONST_convert2tmpl.mk to-tmpl
        cp CONST_create_template/mapserver/*.tmpl mapserver
    fi
    cp CONST_create_template/mapserver/data/Readme.txt mapserver/data/

    ./docker-run --env=NODE_ENV make $MAKE_ARGS upgrade9
    if [ ! -e .UPGRADE_SUCCESS ]
    then
        printdiff
        echo "Fail to upgrade"
        exit 1
    fi
    ./docker-run make $MAKE_ARGS clean-all
    rm --recursive --force .UPGRADE9 .UPGRADE_SUCCESS \
        commons/testgeomapfish_commons.egg-info geoportal/testgeomapfish_geoportal.egg-info
    cd -
    find $1 -type d -empty -delete
    diff --recursive --exclude=.git --exclude=locale ${WORKSPACE}/$2dockerref $1
}

if [ "$1" = "v220-todocker" ]
then
    v220 ${WORKSPACE}/v220-todocker
fi

if [ "$1" = "v220-tonondocker" ]
then
    v220 ${WORKSPACE}/v220-tonondocker non
fi

function v230 {
    DOCKER_ARGS=''
    MAKE_ARGS=''
    if [ "$1" = 'non' ]
    then
        MAKE_ARGS='--makefile=testgeomapfish.mk'
        DOCKER_ARGS='--env=VISIBLE_WEB_HOST=example.com --env=VISIBLE_WEB_PROTOCOL=https --env=VISIBLE_ENTRY_POINT=/'
    fi
    cp travis/old-project.yaml ${WORKSPACE}/v230-$1docker/testgeomapfish/project.yaml.mako
    cd ${WORKSPACE}/v230-$1docker/testgeomapfish
    ./docker-run ${DOCKER_ARGS} make ${MAKE_ARGS} project.yaml
    cd -
    cp travis/from23-config ${WORKSPACE}/v230-$1docker/testgeomapfish/.config
    cd ${WORKSPACE}/v230-$1docker/testgeomapfish
    git add project.yaml.mako .config
    git commit --quiet --message="Start upgrade"
    ./docker-run --env=NODE_ENV make ${MAKE_ARGS} upgrade
    if [ "$1" != 'non' ]
    then
        ./docker-run make --always-make --makefile=CONST_convert2tmpl.mk to-tmpl
        cp CONST_create_template/mapserver/*.tmpl mapserver
        cp {CONST_create_template/,}tilegeneration/config.yaml.tmpl
    fi
    if [ -e .UPGRADE8 ]
    then
        ./docker-run --env=NODE_ENV make ${MAKE_ARGS} upgrade9
    fi
    if [ -e .UPGRADE10 ]
    then
        if [ "$1" != non ]
        then
            cp CONST_create_template/docker-compose.yaml .
            cp CONST_create_template/.env.mako .
        else
            cp CONST_create_template/mapserver/data/Readme.txt mapserver/data/
        fi
        ./docker-run --env=NODE_ENV make ${MAKE_ARGS} upgrade11
    fi
    if [ ! -e .UPGRADE_SUCCESS ]
    then
        printdiff
        echo "Fail to upgrade"
        exit 1
    fi
    cp CONST_create_template/mapserver/data/Readme.txt mapserver/data/
    ./docker-run make ${MAKE_ARGS} clean-all
    rm --recursive --force .UPGRADE* \
        commons/testgeomapfish_commons.egg-info geoportal/testgeomapfish_geoportal.egg-info
    cd -
    find ${WORKSPACE}/v230-$1docker -type d -empty -delete
    diff --recursive --exclude=.git ${WORKSPACE}/$1dockerref ${WORKSPACE}/v230-$1docker
}

if [ "$1" = "v230-docker" ]
then
    v230 ''
fi

if [ "$1" = "v230-nondocker" ]
then
    v230 'non'
fi

if [ "$1" = "cleanup" ]
then
    rm --recursive --force ${WORKSPACE}/nondockerref ${WORKSPACE}/dockerref \
        ${WORKSPACE}/nondocker ${WORKSPACE}/docker \
        ${WORKSPACE}/v220-todocker ${WORKSPACE}/v220-tonondocker \
        ${WORKSPACE}/v230-docker ${WORKSPACE}/v230-nondocker
fi
