#!/bin/bash -e

DEPLOY=false
FINAL=false
BUILD_TAG=false # for rc

if [[ ${TRAVIS_BRANCH} =~ ^(master|[0-9].[0-9])$ ]] && [ ${TRAVIS_PULL_REQUEST} == false ]
then
    DEPLOY=true
fi

if [[ ${TRAVIS_TAG} =~ ^[0-9]+.[0-9]+.[0-9]+(\.[0-9]+)?$ ]]
then
    if [ ${TRAVIS_TAG} != $(python setup.py -V) ]
    then
        echo "The tag name doesn't match with the egg version."
        exit 1
    fi
    DEPLOY=true
    FINAL=true
fi

if [[ ${TRAVIS_TAG} =~ ^[0-9]+.[0-9]+.[0-9]+(\.rc[0-9]+|\.dev[0-9]+)$ ]]
then
    #VERSION=`echo ${TRAVIS_TAG} | sed 's/\(\.rc[0-9]\+\|\.dev[0-9]\+\)$//'`
    if [ ${TRAVIS_TAG} != $(python setup.py -V) ]
    then
        echo "The tag name doesn't match with the egg version."
        exit 1
    fi
    DEPLOY=true
    FINAL=true
    #BUILD_TAG=`echo ${TRAVIS_TAG} | sed 's/^[0-9]\+\.[0-9]\+\.[0-9]\+\.//'`
fi


if [ ${DEPLOY} == true  ] && [ ${TRAVIS_PYTHON_VERSION} == "2.7" ]
then
    echo "[distutils]" > ~/.pypirc
    echo "index-servers = c2c-internal" >> ~/.pypirc
    echo "[c2c-internal]" >> ~/.pypirc
    echo "username:${PIP_USERNAME}" >> ~/.pypirc
    echo "password:${PIP_PASSWORD}" >> ~/.pypirc
    echo "repository:http://pypi.camptocamp.net/internal-pypi/simple" >> ~/.pypirc

    set -x

#    if [ ${BUILD_TAG} != false ]
#    then
#        .build/venv/bin/python setup.py egg_info --no-date --tag-build "${BUILD_TAG}" sdist upload -r c2c-internal
#    else
        if [ ${FINAL} == true ]
        then
            .build/venv/bin/python setup.py egg_info --no-date --tag-build "" sdist upload -r c2c-internal
        else
            .build/venv/bin/python setup.py sdist upload -r c2c-internal
        fi
#    fi

    cd c2cgeoportal/scaffolds/update/+package+/static/mobile/
    tar -czf touch.tar.gz touch
    cd -
    echo "include c2cgeoportal/scaffolds/update/+package+/static/mobile/touch.tar.gz" >> MANIFEST.in
    echo "prune c2cgeoportal/scaffolds/update/+package+/static/mobile/touch" >> MANIFEST.in
    sed -i 's/name="c2cgeoportal",/name="c2cgeoportal-win",/g' setup.py
    git diff

#    if [ ${BUILD_TAG} != false ]
#    then
#        .build/venv/bin/python setup.py egg_info --no-date --tag-build "${BUILD_TAG}" sdist upload -r c2c-internal
#    else
        if [ ${FINAL} == true ]
        then
            .build/venv/bin/python setup.py egg_info --no-date --tag-build "" sdist upload -r c2c-internal
        else
            .build/venv/bin/python setup.py sdist upload -r c2c-internal
        fi
#    fi
fi
