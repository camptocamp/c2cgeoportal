#!/bin/bash -ex

function pcreate {
    if [ "$CI" = true ]
    then
        ./docker-run --share $1 pcreate --scaffold=$2 $1/testgeomapfish \
            --overwrite --ignore-conflicting-name --package-name testgeomapfish > /dev/null
    else
        ./docker-run -ti --share $1 pcreate --scaffold=$2 $1/testgeomapfish \
            --overwrite --ignore-conflicting-name --package-name testgeomapfish
    fi
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
    cd -
}

function createv220 {
    rm --recursive --force $1
    mkdir --parent $1
    cp --recursive /tmp/testgeomapfish $1/testgeomapfish
    pcreate $1 tilecloud_chain
    cd $1/testgeomapfish
    git init
    git remote add origin . # add a fake remote
    git add --all
    git commit --quiet --message="Initial commit"
    cd -
}

if [ $1 = "init" ]
then
    rm --recursive --force $(find c2cgeoportal/scaffolds -name __pycache__)
    export SRID=21781 APACHE_VHOST=test EXTENT=489246.36,78873.44,837119.76,296543.14
    create /tmp/docker
    create /tmp/dockerref
    createnondocker /tmp/nondocker
    createnondocker /tmp/nondockerref
    unset SRID APACHE_VHOST EXTENT
    tar --extract  --bzip2 --file=travis/v220.tar.bz2  --directory=/tmp
    createv220 /tmp/v220-todocker
    createv220 /tmp/v220-tonondocker
fi

if [ $1 = "docker" ]
then
    cd /tmp/docker/testgeomapfish
    ./docker-run make upgrade > /dev/null
    if [ ! -e .UPGRADE_SUCCESS ]
    then
        echo "Fail to upgrade"
        exit 1
    fi
    ./docker-run make clean-all
    rm --recursive --force .UPGRADE10 .UPGRADE_SUCCESS .SUCCESS testgeomapfish.egg-info
    cd -
    diff --recursive --exclude=.git /tmp/dockerref /tmp/docker
fi

if [ $1 = "nondocker" ]
then
    cd /tmp/nondocker/testgeomapfish
    ./docker-run make --makefile=testgeomapfish.mk upgrade > /dev/null
    if [ ! -e .UPGRADE_SUCCESS ]
    then
        echo "Fail to upgrade"
        exit 1
    fi
    ./docker-run make --makefile=testgeomapfish.mk clean-all
    rm --recursive --force .UPGRADE10 .UPGRADE_SUCCESS .SUCCESS testgeomapfish.egg-info
    cd -
    diff --recursive --exclude=.git /tmp/nondockerref /tmp/nondocker
fi

if [ $1 = "todocker" ]
then
    cd /tmp/nondocker/testgeomapfish
    echo "UPGRADE_ARGS += --force-docker --new-makefile=Makefile" > temp.mk
    cat testgeomapfish.mk >> temp.mk
    git rm testgeomapfish.mk
    git add temp.mk
    git commit --quiet --message="Start upgrade"
    ./docker-run make --makefile=temp.mk upgrade > /dev/null
    if [ ! -e .UPGRADE7 ]
    then
        echo "Fail to upgrade"
        exit 1
    fi
    ./docker-run make upgrade8 > /dev/null
    if [ ! -e .UPGRADE_SUCCESS ]
    then
        echo "Fail to upgrade"
        exit 1
    fi
    git rm temp.mk
    ./docker-run make clean-all
    rm --recursive --force .UPGRADE10 .UPGRADE_SUCCESS .SUCCESS testgeomapfish.egg-info
    cd -
    diff --recursive --exclude=.git /tmp/dockerref /tmp/nondocker
fi

if [ $1 = "tonondocker" ]
then
    cd /tmp/docker/testgeomapfish
    cp Makefile tmp
    echo "UPGRADE_ARGS += --nondocker --new-makefile=testgeomapfish.mk" > Makefile
    cat tmp >> Makefile
    rm tmp
    git add Makefile
    git commit --quiet --message="Start upgrade"
    export APACHE_VHOST=test
    ./docker-run make upgrade > /dev/null
    if [ ! -e .UPGRADE7 ]
    then
        echo "Fail to upgrade"
        exit 1
    fi
    ./docker-run make --makefile=testgeomapfish.mk upgrade8 > /dev/null
    if [ ! -e .UPGRADE_SUCCESS ]
    then
        echo "Fail to upgrade"
        exit 1
    fi
    ./docker-run make --makefile=testgeomapfish.mk clean-all
    rm --recursive --force .UPGRADE10 .UPGRADE_SUCCESS .SUCCESS testgeomapfish.egg-info
    cd -
    diff --recursive --exclude=.git /tmp/nondockerref /tmp/docker
fi

function v220 {
    cp docker-run $1/testgeomapfish
    cp travis/v22-project.yaml $1/testgeomapfish/project.yaml.mako
    cd $1/testgeomapfish
    git add docker-run project.yaml.mako
    git commit --quiet --message="Start upgrade"
    make --makefile=testgeomapfish.mk project.yaml
    if [ $2 == non ]
    then
        ./docker-run --image=camptocamp/geomapfish-build \
            c2cupgrade --nondocker --makefile=testgeomapfish.mk
        MAKE_ARGS=--makefile=testgeomapfish.mk
    else
        ./docker-run --image=camptocamp/geomapfish-build \
            c2cupgrade --force-docker --new-makefile=Makefile --makefile=testgeomapfish.mk > /dev/null
    fi
    if [ ! -e .UPGRADE6 ]
    then
        echo "Fail to upgrade"
        exit 1
    fi
    ./docker-run make $MAKE_ARGS upgrade7 > /dev/null
    if [ $2 == non ]
    then
        if [ ! -e .UPGRADE7 ]
        then
            echo "Fail to upgrade"
            exit 1
        fi
        ./docker-run make $MAKE_ARGS upgrade8 > /dev/null
    fi
    if [ ! -e .UPGRADE8 ]
    then
        echo "Fail to upgrade"
        exit 1
    fi
    ./docker-run make $MAKE_ARGS upgrade9 > /dev/null
    if [ ! -e .UPGRADE_SUCCESS ]
    then
        echo "Fail to upgrade"
        exit 1
    fi
    ./docker-run make $MAKE_ARGS clean-all
    rm --recursive --force .UPGRADE10 .UPGRADE_SUCCESS .SUCCESS testgeomapfish.egg-info
    cd -
    diff --recursive --exclude=.git --exclude=LC_MESSAGES /tmp/$2dockerref $1
}

if [ $1 = "v220-todocker" ]
then
    v220 /tmp/v220-todocker
fi

if [ $1 = "v220-tonondocker" ]
then
    v220 /tmp/v220-tonondocker non
fi

if [ $1 = "cleanup" ]
then
    rm -rf /tmp/nondockerref /tmp/dockerref /tmp/nondocker /tmp/docker /tmp/v220-todocker /tmp/v220-tonondocker
fi
