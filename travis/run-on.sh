#!/bin/bash -e

# Usage travis/run-on.sh directory command

# The goal is to run the command on an other directory
# and return to the original directory withouts losing the error code

pushd `pwd`

cd $1

$2

ERROR=$?

popd

exit $ERROR
