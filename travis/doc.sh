#!/bin/bash -e

DOC=false

if [[ ${TRAVIS_BRANCH} =~ ^(master|[0-9]+.[0-9]+)$ ]] && [ ${TRAVIS_PULL_REQUEST} == false ]
then
    DOC=true
fi


echo == Build the doc ==
if [ ${DOC} == false ]
then
    TRAVIS_BRANCH=master
fi

GIT_REV=`git log | head -n 1 | awk '{{print $2}}'`
git fetch origin gh-pages:gh-pages
git checkout gh-pages

mkdir -p ${TRAVIS_BRANCH}
rm -rf ${TRAVIS_BRANCH}/*
mv doc/_build/html/* ${TRAVIS_BRANCH}

if [ ${DOC} == true ]
then
    git add --all ${TRAVIS_BRANCH}
    git commit -m "Update documentation for the revision ${TRAVIS_COMMIT}"
    git push origin gh-pages
else
    git checkout master/searchindex.js
    git status
    git diff
    git reset --hard
fi

# back to the original branch
git checkout ${GIT_REV}
