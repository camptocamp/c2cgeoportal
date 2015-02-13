#!/bin/bash -ex

DEPLOY=false
EGG_INFO=""

if [[ $TRAVIS_BRANCH =~ ^(master|[0-9].[0-9])$ ]] && [ $TRAVIS_PULL_REQUEST == false ]
then
    DEPLOY=true
fi

if [[ $TRAVIS_TAG =~ ^[0-9].[0-9]+.[0-9]$ ]]
then
    if [ $TRAVIS_TAG != $(python setup.py -V) ]
    then
        echo "The tag name doesn't match with the egg version."
        exit 1
    fi
    DEPLOY=true
    EGG_INFO="egg_info --no-date --tag-build"
fi

if [ $DEPLOY == true  ] && [ $TRAVIS_PYTHON_VERSION == "2.7" ]
then
    echo "[distutils]" > ~/.pypirc
    echo "index-servers = c2c-internal" >> ~/.pypirc
    echo "[c2c-internal]" >> ~/.pypirc
    echo "username:$PIP_USERNAME" >> ~/.pypirc
    echo "password:$PIP_PASSWORD" >> ~/.pypirc
    echo "repository:http://pypi.camptocamp.net/internal-pypi/simple" >> ~/.pypirc

    .build/venv/bin/python setup.py $EGG_INFO -q sdist upload -r c2c-internal

    cd c2cgeoportal/scaffolds/update/+package+/static/mobile/
    tar -czf touch.tar.gz touch
    cd -
    echo "include c2cgeoportal/scaffolds/update/+package+/static/mobile/touch.tar.gz" >> MANIFEST.in
    echo "prune c2cgeoportal/scaffolds/update/+package+/static/mobile/touch" >> MANIFEST.in
    sed -i "s/name='c2cgeoportal',/name='c2cgeoportal-win',/g" setup.py
    .build/venv/bin/python setup.py $EGG_INFO -d sdist upload -r c2c-internal
fi
