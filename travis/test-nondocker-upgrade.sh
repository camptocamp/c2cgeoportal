#!/bin/bash -ex

export VERSION=$(python setup.py --version)

cd /tmp/travis/nondockertestgeomapfish/

#make -f travis.mk upgrade
#for STEP in {1..13}:
#do
#    make -f travis.mk upgrade${STEP}
#done
