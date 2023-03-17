#!/bin/bash -ex

GIT_REV=$(git log | head --lines=1 | awk '{{print $2}}')

PUBLISH=false
BRANCH=${MAIN_BRANCH}

if [[ ${BRANCH_NAME} =~ ^(master|[0-9]+.[0-9]+)$ ]]; then
    PUBLISH=true
fi

echo == Build the doc ==

git fetch origin gh-pages:gh-pages
git checkout gh-pages

if [ -e ${MAIN_BRANCH} ]; then
    git rm -r --force -- ${MAIN_BRANCH}
fi
mkdir --parent ${MAIN_BRANCH}
mv doc/_build/html/* ${MAIN_BRANCH}

if [ ${PUBLISH} == true ]; then
    git add --all ${MAIN_BRANCH}
    git commit --message="Update documentation for the revision ${GIT_REV}" | true
    git push origin gh-pages
else
    git checkout ${MAIN_BRANCH}/searchindex.js || true
    git checkout ${MAIN_BRANCH}/_sources || true
    git checkout ${MAIN_BRANCH}/_static || true
    git status
    git diff
    git reset --hard
fi

# Back to the original branch
git checkout ${GIT_REV}
