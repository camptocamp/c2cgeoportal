#!/bin/bash -e

# Usage travis/run-on.sh directory command

# The goal is to run the command on an other directory
# and return to the original directory withouts losing the error code

pushd $(pwd) > /dev/null

cd $1

shift

$*

ERROR=$?

popd > /dev/null

exit $ERROR
