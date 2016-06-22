#!/bin/bash -ex

DOC=false
BRANCH=master

if [[ ${TRAVIS_BRANCH} =~ ^(master|[0-9]+.[0-9]+)$ ]] && [ ${TRAVIS_PULL_REQUEST} == false ]
then
    DOC=true
    BRANCH=${TRAVIS_BRANCH}
fi


echo == Build the doc ==

GIT_REV=`git log | head -n 1 | awk '{{print $2}}'`
git fetch origin gh-pages:gh-pages
git checkout gh-pages

mkdir -p ${BRANCH}
rm -rf ${BRANCH}/*
mv doc/_build/html/* ${BRANCH}

if [ ${DOC} == true ]
then
    git add --all ${BRANCH}
    git commit -m "Update documentation for the revision ${TRAVIS_COMMIT}" | true
    git push origin gh-pages
else
    git checkout master/searchindex.js
    git status
    git diff
    git reset --hard
fi

# back to the original branch
git checkout ${GIT_REV}
