#!/bin/bash

if [[ $TRAVIS_BRANCH$TRAVIS_PULL_REQUEST =~ ^(master|[0-9].[0-9])false$ ]]; then
    echo "[distutils]" > ~/.pypirc
    echo "index-servers = c2c-internal" >> ~/.pypirc
    echo "[c2c-internal]" >> ~/.pypirc
    echo "username:$PIP_USERNAME" >> ~/.pypirc
    echo "password:$PIP_PASSWORD" >> ~/.pypirc
    echo "repository:http://pypi.camptocamp.net/internal-pypi/simple" >> ~/.pypirc

    ./buildout/bin/python setup.py sdist upload -r c2c-internal

    cd c2cgeoportal/scaffolds/update/+package+/static/mobile/
    tar -czvf touch.tar.gz touch
    cd -
    echo "include c2cgeoportal/scaffolds/update/+package+/static/mobile/touch.tar.gz" >> MANIFEST.in
    echo "prune c2cgeoportal/scaffolds/update/+package+/static/mobile/touch" >> MANIFEST.in
    sed -i "s/name='c2cgeoportal',/name='c2cgeoportal-win',/g" setup.py
    ./buildout/bin/python setup.py sdist upload -r c2c-internal
fi
