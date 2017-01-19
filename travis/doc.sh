#!/bin/bash -ex

./docker-run make -f travis.mk doc

DOC=false
BRANCH=master

if [[ ${TRAVIS_BRANCH} =~ ^(master|[0-9]+.[0-9]+)$ ]] && [ ${TRAVIS_PULL_REQUEST} == false ]
then
    DOC=true
    BRANCH=${TRAVIS_BRANCH}
fi


echo == Build the doc ==

git fetch origin gh-pages:gh-pages
git checkout gh-pages

git rm -r --force -- ${BRANCH}
mkdir --parent ${BRANCH}
mv doc/_build/html/* ${BRANCH}

if [ ${DOC} == true ]
then
    git add --all ${BRANCH}
    git commit --message="Update documentation for the revision ${TRAVIS_COMMIT}" | true
    git push origin gh-pages
else
    git checkout master/searchindex.js || true
    git status
    git diff
    git reset --hard
fi

# back to the original branch
git checkout ${GIT_REV}
