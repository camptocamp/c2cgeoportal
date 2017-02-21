#!/bin/bash -ex

export VERSION=$(python setup.py --version)

cd /tmp/travis/testgeomapfish/

make -f travis.mk upgrade1
make -f travis.mk upgrade2
