#!/bin/bash -ex

./docker-run make doc

DOC=false
BRANCH=${MAIN_BRANCH}

if [[ ${TRAVIS_BRANCH} =~ ^(master|[0-9]+.[0-9]+)$ ]] && [ ${TRAVIS_PULL_REQUEST} == false ]
then
    DOC=true
fi


echo == Build the doc ==

git fetch origin gh-pages:gh-pages
git checkout gh-pages

if [ -e ${BRANCH} ]
then
    git rm -r --force -- ${BRANCH}
fi
mkdir --parent ${BRANCH}
mv doc/_build/html/* ${BRANCH}

if [ ${DOC} == true ]
then
    git add --all ${BRANCH}
    git commit --message="Update documentation for the revision ${TRAVIS_COMMIT}" | true
    git push origin gh-pages
else
    git checkout ${BRANCH}/searchindex.js || true
    git checkout ${BRANCH}/_sources || true
    git checkout ${BRANCH}/_static || true
    git status
    git diff
    git reset --hard
fi

# back to the original branch
git checkout ${GIT_REV}
