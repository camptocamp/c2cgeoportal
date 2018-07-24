#!/bin/bash -ex

# create fake vhosts
sudo mkdir -p /var/www/vhosts/test/conf
sudo chmod g+w,o+w /var/www/vhosts/test/conf

cp travis/build.mk /tmp/test/travis.mk

cd /tmp/test/

sed -e 's@^c2cgeoportal==.*$@/home/travis/build/camptocamp/c2cgeoportal@' -i CONST_requirements.txt

git config --global user.name "Travis"
git config --global user.email "travis@example.com"
git init
git add -A
git submodule add https://github.com/camptocamp/cgxp.git test/static/lib/cgxp
git commit -q -m "Initial commit"

make -f travis.mk build

echo "Build complete"

cd -
