#!/bin/bash

if [[ $TRAVIS_BRANCH$TRAVIS_PULL_REQUEST =~ ^(master|[0-9].[0-9])false$ ]]; then
    echo "[distutils]" > ~/.pypirc
    echo "index-servers = c2c-internal" >> ~/.pypirc
    echo "[c2c-internal]" >> ~/.pypirc
    echo "username:$PIP_USERNAME" >> ~/.pypirc
    echo "password:$PIP_PASSWORD" >> ~/.pypirc
    echo "repository:http://pypi.camptocamp.net/internal-pypi/simple" >> ~/.pypirc

    ./buildout/bin/python setup.py sdist upload -r c2c-internal
fi
