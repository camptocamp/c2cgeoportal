#!/bin/bash -e

DEPLOY=false
FINAL=false
BUILD_TAG=false # for rc

if [[ ${TRAVIS_BRANCH} =~ ^(master|[0-9].[0-9])$ ]] && [ ${TRAVIS_PULL_REQUEST} == false ]
then
    DEPLOY=true
fi

if [[ ${TRAVIS_TAG} =~ ^[0-9].[0-9]+.[0-9]$ ]]
then
    if [ ${TRAVIS_TAG} != $(python setup.py -V) ]
    then
        echo "The tag name doesn't match with the egg version."
        exit 1
    fi
    DEPLOY=true
    FINAL=true
fi

if [[ ${TRAVIS_TAG} =~ ^[0-9].[0-9]+.0rc[0-9]$ ]]
then
    VERSION=`echo ${TRAVIS_TAG} | awk -Frc '{print $1}'`
    if [ ${VERSION} != $(python setup.py -V) ]
    then
        echo "The tag name doesn't match with the egg version."
        exit 1
    fi
    DEPLOY=true
    BUILD_TAG=rc`echo ${TRAVIS_TAG} | awk -Frc '{print $2}'`
fi

if [ ${DEPLOY} == true  ] && [ ${TRAVIS_PYTHON_VERSION} == "2.7" ]
then
    set -x

    if [ ${BUILD_TAG} != false ]
    then
        .build/venv/bin/python setup.py egg_info --no-date --tag-build "${BUILD_TAG}" bdist_wheel
    else
    if [ ${FINAL} == true ]
        then
            .build/venv/bin/python setup.py egg_info --no-date --tag-build "" bdist_wheel
        else
            .build/venv/bin/python setup.py bdist_wheel
        fi
    fi

    git checkout gh-pages
    mv dist/*.whl .
    pip install magnum-pi
    makeindex .
    git add *.whl
    git add index
    git commit -m "Deploy the revision ${TRAVIS_COMMIT}"
fi

git push origin gh-pages
