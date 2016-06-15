#!/bin/bash -ex

cd /tmp/travis/testgeomapfish/

make -f travis.mk build
echo "Build complete"

git add testgeomapfish/locale/*/LC_MESSAGES/testgeomapfish-*.po
git commit --message="Add location"
