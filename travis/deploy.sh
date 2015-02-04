#!/bin/bash -ex

DEPLOY=false
EGG_INFO=''

if [[ $TRAVIS_BRANCH$TRAVIS_PULL_REQUEST =~ ^(master|[0-9].[0-9])false$ ]]
then
    DEPLOY=true
elif [ $TRAVIS_TAG = `.build/venv/bin/python setup.py --version` ]
then
    DEPLOY=true
    EGG_INFO='egg_info --no-date --tag-build ""'
fi

if [ $DEPLOY = true ]
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
